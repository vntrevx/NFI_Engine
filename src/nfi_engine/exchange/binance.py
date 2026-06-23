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
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import AccountSnapshot, StakeAmount, TradingMode
from nfi_engine.exchange.errors import ExchangeError, ExchangeErrorCode

BINANCE_FAPI_BASE_URL: Final = "https://fapi.binance.com"
BINANCE_FAPI_TESTNET_BASE_URL: Final = "https://testnet.binancefuture.com"
BALANCE_PATH: Final = "/fapi/v3/balance"
DEFAULT_RECV_WINDOW_MS: Final = 5000
HTTP_CLIENT_ERROR_MIN: Final = 400
AUTH_FAILURE_STATUSES: Final = frozenset({401, 403})
HTTP_LIMITS: Final = httpx.Limits(
    max_connections=10,
    max_keepalive_connections=4,
    keepalive_expiry=30.0,
)
HTTP_TIMEOUT: Final = httpx.Timeout(connect=5.0, read=10.0, write=5.0, pool=5.0)

type QueryParams = tuple[tuple[str, str], ...]
type TimestampProvider = Callable[[], int]


def _timestamp_ms() -> int:
    return int(datetime.now(UTC).timestamp() * 1000)


class BinanceHttpClient(Protocol):
    async def get(
        self,
        url: str,
        *,
        params: QueryParams,
        headers: Mapping[str, str],
    ) -> httpx.Response: ...


class BinanceFuturesBalanceAsset(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)

    asset: str
    balance: Decimal
    available_balance: Decimal = Field(alias="availableBalance")


BALANCE_PAYLOAD_ADAPTER: Final = TypeAdapter(tuple[BinanceFuturesBalanceAsset, ...])


@dataclass(frozen=True, slots=True)
class BinanceFuturesBalanceAdapter:
    api_key: str
    api_secret: str
    quote_asset: str
    client: BinanceHttpClient | None = None
    base_url: str = BINANCE_FAPI_TESTNET_BASE_URL
    recv_window_ms: int = DEFAULT_RECV_WINDOW_MS
    timestamp_ms: TimestampProvider = _timestamp_ms

    @classmethod
    def from_settings(cls, *, settings: RuntimeSettings) -> BinanceFuturesBalanceAdapter:
        match settings.exchange.trading_mode:
            case TradingMode.FUTURES:
                pass
            case TradingMode.SPOT:
                raise ExchangeError(
                    code=ExchangeErrorCode.EXCHANGE_RESPONSE_INVALID,
                    message="Binance wallet adapter currently supports futures balance only.",
                )
        if settings.exchange.api_key is None or settings.exchange.api_secret is None:
            raise ExchangeError(
                code=ExchangeErrorCode.EXCHANGE_AUTH_FAILED,
                message="Binance wallet adapter requires exchange API credentials.",
            )
        return cls(
            api_key=settings.exchange.api_key,
            api_secret=settings.exchange.api_secret,
            quote_asset=settings.pairlist.quote_asset,
            base_url=(
                BINANCE_FAPI_TESTNET_BASE_URL
                if settings.exchange.testnet
                else BINANCE_FAPI_BASE_URL
            ),
        )

    async def fetch_balance(self) -> AccountSnapshot:
        if self.client is not None:
            return await self._fetch_with_client(self.client)
        async with httpx.AsyncClient(
            base_url=self.base_url,
            limits=HTTP_LIMITS,
            timeout=HTTP_TIMEOUT,
            follow_redirects=False,
        ) as client:
            return await self._fetch_with_client(client)

    async def _fetch_with_client(self, client: BinanceHttpClient) -> AccountSnapshot:
        signed_at = self.timestamp_ms()
        try:
            response = await client.get(
                BALANCE_PATH,
                params=self._signed_params(timestamp_ms=signed_at),
                headers={"X-MBX-APIKEY": self.api_key},
            )
        except httpx.TransportError as exc:
            raise ExchangeError(
                code=ExchangeErrorCode.EXCHANGE_HTTP_ERROR,
                message="Binance balance request failed at transport boundary.",
            ) from exc
        _raise_for_status(response.status_code)
        assets = _parse_balance_assets(response.content)
        quote_asset = _quote_asset(assets=assets, asset=self.quote_asset)
        return AccountSnapshot(
            captured_at=datetime.fromtimestamp(signed_at / 1000, tz=UTC),
            equity=StakeAmount(quote_asset.balance),
            available=StakeAmount(quote_asset.available_balance),
            positions=(),
        )

    def _signed_params(self, *, timestamp_ms: int) -> QueryParams:
        params: QueryParams = (
            ("recvWindow", str(self.recv_window_ms)),
            ("timestamp", str(timestamp_ms)),
        )
        signature = hmac.new(
            self.api_secret.encode(),
            urlencode(params).encode(),
            sha256,
        ).hexdigest()
        return (*params, ("signature", signature))


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
        message=f"Binance balance request failed with status {status_code}.",
    )


def _parse_balance_assets(content: bytes) -> tuple[BinanceFuturesBalanceAsset, ...]:
    try:
        return BALANCE_PAYLOAD_ADAPTER.validate_json(content)
    except ValidationError as exc:
        raise ExchangeError(
            code=ExchangeErrorCode.EXCHANGE_RESPONSE_INVALID,
            message="Binance balance response shape is invalid.",
        ) from exc


def _quote_asset(
    *,
    assets: tuple[BinanceFuturesBalanceAsset, ...],
    asset: str,
) -> BinanceFuturesBalanceAsset:
    for candidate in assets:
        if candidate.asset == asset:
            return candidate
    raise ExchangeError(
        code=ExchangeErrorCode.EXCHANGE_RESPONSE_INVALID,
        message=f"Binance balance response did not include {asset}.",
    )
