from __future__ import annotations

import hmac
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from typing import ClassVar, Final, Protocol
from urllib.parse import urlencode

import httpx
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import OrderState, OrderType, PositionSide, TradingMode
from nfi_engine.exchange.binance import (
    BINANCE_FAPI_BASE_URL,
    DEFAULT_RECV_WINDOW_MS,
    HTTP_CLIENT_ERROR_MIN,
    HTTP_LIMITS,
    HTTP_TIMEOUT,
)
from nfi_engine.exchange.live_canary_order_models import (
    LiveCanaryClientError,
    LiveCanaryExchangeOrder,
    LiveCanaryOrderRequest,
)

ORDER_PATH: Final = "/fapi/v1/order"
AUTH_FAILURE_STATUSES: Final = frozenset({401, 403})
type QueryParams = tuple[tuple[str, str], ...]
type TimestampProvider = Callable[[], int]


def _timestamp_ms() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)


class BinanceLiveCanaryHttpClient(Protocol):
    async def post(
        self,
        url: str,
        *,
        params: QueryParams,
        headers: Mapping[str, str],
    ) -> httpx.Response: ...

    async def get(
        self,
        url: str,
        *,
        params: QueryParams,
        headers: Mapping[str, str],
    ) -> httpx.Response: ...


class BinanceOrderPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)

    order_id: str = Field(alias="orderId")
    client_order_id: str = Field(alias="clientOrderId")
    symbol: str
    side: str
    type: str
    status: str
    orig_qty: Decimal = Field(alias="origQty")
    executed_qty: Decimal = Field(alias="executedQty")
    avg_price: Decimal | None = Field(default=None, alias="avgPrice")
    reduce_only: bool = Field(default=False, alias="reduceOnly")


@dataclass(frozen=True, slots=True)
class BinanceFuturesLiveCanaryClient:
    api_key: str
    api_secret: str
    client: BinanceLiveCanaryHttpClient | None = None
    base_url: str = BINANCE_FAPI_BASE_URL
    recv_window_ms: int = DEFAULT_RECV_WINDOW_MS
    timestamp_ms: TimestampProvider = _timestamp_ms

    @classmethod
    def from_settings(cls, settings: RuntimeSettings) -> BinanceFuturesLiveCanaryClient:
        if settings.exchange.name.casefold() != "binance":
            code = "LIVE_CANARY_EXCHANGE_UNSUPPORTED"
            message = "Live canary order lane currently supports Binance futures only."
            raise LiveCanaryClientError(code, message)
        if settings.exchange.trading_mode is not TradingMode.FUTURES:
            code = "LIVE_CANARY_TRADING_MODE_UNSUPPORTED"
            message = "Live canary order lane currently supports futures only."
            raise LiveCanaryClientError(code, message)
        if settings.exchange.testnet:
            code = "LIVE_CANARY_PRODUCTION_REQUIRED"
            message = "Live canary order lane requires exchange.testnet=false."
            raise LiveCanaryClientError(code, message)
        if settings.exchange.api_key is None or settings.exchange.api_secret is None:
            code = "LIVE_CANARY_CREDENTIALS_MISSING"
            message = "Live canary order lane requires owner exchange credentials."
            raise LiveCanaryClientError(code, message)
        return cls(api_key=settings.exchange.api_key, api_secret=settings.exchange.api_secret)

    async def submit_order(self, request: LiveCanaryOrderRequest) -> LiveCanaryExchangeOrder:
        payload = await self._request("POST", request=request)
        return _exchange_order_from_payload(payload, request=request)

    async def fetch_order(self, request: LiveCanaryOrderRequest) -> LiveCanaryExchangeOrder:
        payload = await self._request("GET", request=request)
        return _exchange_order_from_payload(payload, request=request)

    async def _request(
        self,
        method: str,
        *,
        request: LiveCanaryOrderRequest,
    ) -> BinanceOrderPayload:
        signed_at = self.timestamp_ms()
        params = _signed_order_params(
            request=request,
            recv_window_ms=self.recv_window_ms,
            timestamp_ms=signed_at,
            api_secret=self.api_secret,
            include_order_payload=method == "POST",
        )
        try:
            async with httpx.AsyncClient(
                base_url=self.base_url,
                limits=HTTP_LIMITS,
                timeout=HTTP_TIMEOUT,
                follow_redirects=False,
            ) as default_client:
                client = self.client or default_client
                response = await _send(client, method, params=params, api_key=self.api_key)
        except httpx.TransportError as exc:
            code = "LIVE_CANARY_EXCHANGE_HTTP_ERROR"
            message = "Binance live canary request failed at transport boundary."
            raise LiveCanaryClientError(code, message) from exc
        _raise_for_status(response.status_code)
        return _parse_order_payload(response.content)


async def _send(
    client: BinanceLiveCanaryHttpClient,
    method: str,
    *,
    params: QueryParams,
    api_key: str,
) -> httpx.Response:
    headers = {"X-MBX-APIKEY": api_key}
    if method == "POST":
        return await client.post(ORDER_PATH, params=params, headers=headers)
    return await client.get(ORDER_PATH, params=params, headers=headers)


def _signed_order_params(
    *,
    request: LiveCanaryOrderRequest,
    recv_window_ms: int,
    timestamp_ms: int,
    api_secret: str,
    include_order_payload: bool,
) -> QueryParams:
    base = _order_params(request, recv_window_ms, timestamp_ms, include_order_payload)
    signature = hmac.new(api_secret.encode(), urlencode(base).encode(), sha256).hexdigest()
    return (*base, ("signature", signature))


def _order_params(
    request: LiveCanaryOrderRequest,
    recv_window_ms: int,
    timestamp_ms: int,
    include_order_payload: bool,
) -> QueryParams:
    common: QueryParams = (
        ("symbol", _binance_symbol(request.pair)),
        ("origClientOrderId", request.client_order_id),
        ("recvWindow", str(recv_window_ms)),
        ("timestamp", str(timestamp_ms)),
    )
    if not include_order_payload:
        return common
    return (
        ("symbol", _binance_symbol(request.pair)),
        ("side", _binance_side(request.side)),
        ("type", _binance_type(request.order_type)),
        ("quantity", str(request.quantity)),
        ("reduceOnly", "true" if request.reduce_only else "false"),
        ("newClientOrderId", request.client_order_id),
        ("recvWindow", str(recv_window_ms)),
        ("timestamp", str(timestamp_ms)),
    )


def _exchange_order_from_payload(
    payload: BinanceOrderPayload,
    *,
    request: LiveCanaryOrderRequest,
) -> LiveCanaryExchangeOrder:
    return LiveCanaryExchangeOrder(
        exchange_order_id=payload.order_id,
        client_order_id=payload.client_order_id,
        pair=request.pair,
        side=_position_side(payload.side),
        order_type=request.order_type,
        state=_order_state(payload.status),
        quantity=payload.orig_qty,
        filled_quantity=payload.executed_qty,
        average_price=payload.avg_price,
        reduce_only=payload.reduce_only,
        raw_status_code=payload.status,
    )


def _parse_order_payload(content: bytes) -> BinanceOrderPayload:
    try:
        return BinanceOrderPayload.model_validate_json(content)
    except ValidationError as exc:
        code = "LIVE_CANARY_EXCHANGE_RESPONSE_INVALID"
        message = "Binance live canary order response shape is invalid."
        raise LiveCanaryClientError(code, message) from exc


def _raise_for_status(status_code: int) -> None:
    if status_code < HTTP_CLIENT_ERROR_MIN:
        return
    if status_code in AUTH_FAILURE_STATUSES:
        code = "LIVE_CANARY_EXCHANGE_AUTH_FAILED"
        message = "Binance rejected the API key, IP allowlist, or permissions."
        raise LiveCanaryClientError(code, message)
    code = "LIVE_CANARY_EXCHANGE_HTTP_ERROR"
    message = f"Binance live canary request failed with status {status_code}."
    raise LiveCanaryClientError(code, message)


def _binance_symbol(pair: str) -> str:
    return pair.split(":", maxsplit=1)[0].replace("/", "").upper()


def _binance_side(side: PositionSide) -> str:
    if side is PositionSide.LONG:
        return "BUY"
    return "SELL"


def _binance_type(order_type: OrderType) -> str:
    return order_type.value.upper()


def _position_side(side: str) -> PositionSide:
    if side == "BUY":
        return PositionSide.LONG
    return PositionSide.SHORT


def _order_state(status: str) -> OrderState:
    normalized = status.casefold()
    if normalized == "new":
        return OrderState.OPEN
    if normalized == "partially_filled":
        return OrderState.PARTIALLY_FILLED
    if normalized == "filled":
        return OrderState.FILLED
    if normalized == "canceled":
        return OrderState.CANCELED
    if normalized in {"rejected", "expired"}:
        return OrderState.REJECTED
    return OrderState.CREATED
