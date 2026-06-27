from __future__ import annotations

import hmac
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Final, Protocol, assert_never
from urllib.parse import urlencode

import httpx

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import OrderState, OrderType, PositionSide, TradingMode, TradingPair
from nfi_engine.exchange.binance import (
    BINANCE_FAPI_TESTNET_BASE_URL,
    DEFAULT_RECV_WINDOW_MS,
    HTTP_LIMITS,
    HTTP_TIMEOUT,
)
from nfi_engine.exchange.errors import ExchangeError, ExchangeErrorCode
from nfi_engine.exchange.models import ExchangeOrder, ExchangeOrderRequest

TEST_ORDER_PATH: Final = "/fapi/v1/order/test"
HTTP_CLIENT_ERROR_MIN: Final = 400
AUTH_FAILURE_STATUSES: Final = frozenset({401, 403})

type QueryParams = tuple[tuple[str, str], ...]
type TimestampProvider = Callable[[], int]


def _timestamp_ms() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)


class BinanceOrderTestHttpClient(Protocol):
    async def post(
        self,
        url: str,
        *,
        params: QueryParams,
        headers: Mapping[str, str],
    ) -> httpx.Response: ...


@dataclass(frozen=True, slots=True)
class BinanceFuturesOrderTestAdapter:
    api_key: str
    api_secret: str
    client: BinanceOrderTestHttpClient | None = None
    base_url: str = BINANCE_FAPI_TESTNET_BASE_URL
    recv_window_ms: int = DEFAULT_RECV_WINDOW_MS
    timestamp_ms: TimestampProvider = _timestamp_ms

    @classmethod
    def from_settings(cls, *, settings: RuntimeSettings) -> BinanceFuturesOrderTestAdapter:
        match settings.exchange.trading_mode:
            case TradingMode.FUTURES:
                pass
            case TradingMode.SPOT:
                raise ExchangeError(
                    code=ExchangeErrorCode.EXCHANGE_RESPONSE_INVALID,
                    message="Binance order-test adapter currently supports futures only.",
                )
            case unreachable:
                assert_never(unreachable)
        if not settings.exchange.testnet:
            raise ExchangeError(
                code=ExchangeErrorCode.LIVE_EXCHANGE_DISABLED_FOR_MILESTONE,
                message="Binance order-test adapter requires testnet=true.",
            )
        if settings.exchange.api_key is None or settings.exchange.api_secret is None:
            raise ExchangeError(
                code=ExchangeErrorCode.EXCHANGE_AUTH_FAILED,
                message="Binance order-test adapter requires exchange API credentials.",
            )
        return cls(api_key=settings.exchange.api_key, api_secret=settings.exchange.api_secret)

    async def test_order(self, request: ExchangeOrderRequest) -> ExchangeOrder:
        if self.client is not None:
            return await self._test_with_client(self.client, request=request)
        async with httpx.AsyncClient(
            base_url=self.base_url,
            limits=HTTP_LIMITS,
            timeout=HTTP_TIMEOUT,
            follow_redirects=False,
        ) as client:
            return await self._test_with_client(client, request=request)

    async def _test_with_client(
        self,
        client: BinanceOrderTestHttpClient,
        *,
        request: ExchangeOrderRequest,
    ) -> ExchangeOrder:
        signed_at = self.timestamp_ms()
        try:
            response = await client.post(
                TEST_ORDER_PATH,
                params=self.signed_order_params(request=request, timestamp_ms=signed_at),
                headers={"X-MBX-APIKEY": self.api_key},
            )
        except httpx.TransportError as exc:
            raise ExchangeError(
                code=ExchangeErrorCode.EXCHANGE_HTTP_ERROR,
                message="Binance test-order request failed at transport boundary.",
            ) from exc
        _raise_for_status(response.status_code)
        return ExchangeOrder(
            order_id=f"binance-test-{signed_at}",
            pair=request.pair,
            side=request.side,
            order_type=request.order_type,
            state=OrderState.OPEN,
            quantity=request.quantity,
            price=request.price,
            filled_price=None,
            live_exchange=False,
        )

    def signed_order_params(
        self,
        *,
        request: ExchangeOrderRequest,
        timestamp_ms: int,
    ) -> QueryParams:
        params = _order_params(
            request=request,
            recv_window_ms=self.recv_window_ms,
            timestamp_ms=timestamp_ms,
        )
        signature = hmac.new(
            self.api_secret.encode(),
            urlencode(params).encode(),
            sha256,
        ).hexdigest()
        return (*params, ("signature", signature))


def _order_params(
    *,
    request: ExchangeOrderRequest,
    recv_window_ms: int,
    timestamp_ms: int,
) -> QueryParams:
    match request.order_type:
        case OrderType.LIMIT:
            if request.price is None:
                raise ExchangeError(
                    code=ExchangeErrorCode.ORDER_PAYLOAD_INVALID,
                    message="Binance LIMIT test order requires a price.",
                )
            return (
                ("symbol", _binance_symbol(request.pair)),
                ("side", _binance_side(request.side)),
                ("type", "LIMIT"),
                ("timeInForce", "GTC"),
                ("quantity", str(request.quantity)),
                ("price", str(request.price)),
                ("recvWindow", str(recv_window_ms)),
                ("timestamp", str(timestamp_ms)),
            )
        case OrderType.MARKET:
            return (
                ("symbol", _binance_symbol(request.pair)),
                ("side", _binance_side(request.side)),
                ("type", "MARKET"),
                ("quantity", str(request.quantity)),
                ("recvWindow", str(recv_window_ms)),
                ("timestamp", str(timestamp_ms)),
            )
        case unreachable:
            assert_never(unreachable)


def _binance_symbol(pair: TradingPair) -> str:
    base_quote = str(pair.normalized).split(":", maxsplit=1)[0]
    return base_quote.replace("/", "").upper()


def _binance_side(side: PositionSide) -> str:
    match side:
        case PositionSide.LONG:
            return "BUY"
        case PositionSide.SHORT:
            return "SELL"
        case unreachable:
            assert_never(unreachable)


def _raise_for_status(status_code: int) -> None:
    if status_code < HTTP_CLIENT_ERROR_MIN:
        return
    if status_code in AUTH_FAILURE_STATUSES:
        raise ExchangeError(
            code=ExchangeErrorCode.EXCHANGE_AUTH_FAILED,
            message="Binance rejected the API key, IP allowlist, or permissions.",
        )
    raise ExchangeError(
        code=ExchangeErrorCode.EXCHANGE_HTTP_ERROR,
        message=f"Binance test-order request failed with status {status_code}.",
    )
