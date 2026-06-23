from __future__ import annotations

import hmac
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
from urllib.parse import urlencode

import httpx
import pytest

from nfi_engine.config import ExchangeSettings, RuntimeSettings
from nfi_engine.domain import AccountSnapshot, TradingMode
from nfi_engine.exchange.binance import BinanceFuturesBalanceAdapter
from nfi_engine.exchange.errors import ExchangeError, ExchangeErrorCode

pytestmark = pytest.mark.anyio

FIXED_TIMESTAMP_MS = 1_700_000_000_000
QUOTE_ASSET = "USDT"
API_KEY = "test-binance-key"
SIGNING_KEY = "test-binance-signing-key"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_binance_futures_adapter_fetches_quote_balance_read_only() -> None:
    # Given: a signed Binance futures balance adapter with a wire-level fake.
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json=[
                {"asset": "BTC", "balance": "0.25", "availableBalance": "0.20"},
                {"asset": "USDT", "balance": "1234.50", "availableBalance": "1200.25"},
            ],
        )

    async with _client(handler) as client:
        adapter = BinanceFuturesBalanceAdapter(
            api_key=API_KEY,
            api_secret=SIGNING_KEY,
            quote_asset=QUOTE_ASSET,
            client=client,
            timestamp_ms=_fixed_timestamp_ms,
        )

        # When: the read-only wallet snapshot is fetched.
        snapshot = await adapter.fetch_balance()

    # Then: only the signed balance endpoint is called and the quote asset is normalized.
    assert isinstance(snapshot, AccountSnapshot)
    assert snapshot.captured_at == datetime.fromtimestamp(FIXED_TIMESTAMP_MS / 1000, tz=UTC)
    assert snapshot.equity == Decimal("1234.50")
    assert snapshot.available == Decimal("1200.25")
    assert snapshot.positions == ()
    assert len(requests) == 1
    request = requests[0]
    assert request.method == "GET"
    assert request.url.path == "/fapi/v3/balance"
    assert request.headers["X-MBX-APIKEY"] == API_KEY
    assert request.url.params["recvWindow"] == "5000"
    assert request.url.params["timestamp"] == str(FIXED_TIMESTAMP_MS)
    assert request.url.params["signature"] == _signature(
        (("recvWindow", "5000"), ("timestamp", str(FIXED_TIMESTAMP_MS))),
    )
    assert SIGNING_KEY not in str(request.url)


def test_binance_futures_adapter_uses_testnet_base_url_from_settings() -> None:
    # Given: Binance futures settings are explicitly scoped to testnet.
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="binance",
            trading_mode=TradingMode.FUTURES,
            testnet=True,
            api_key=API_KEY,
            api_secret=SIGNING_KEY,
        ),
    )

    # When: the wallet adapter is created from runtime settings.
    adapter = BinanceFuturesBalanceAdapter.from_settings(settings=settings)

    # Then: no wallet-balance call can default to the production futures REST URL.
    assert adapter.base_url == "https://testnet.binancefuture.com"


def test_binance_futures_adapter_defaults_to_testnet_base_url() -> None:
    # Given / When: the adapter is constructed without an explicit network base URL.
    adapter = BinanceFuturesBalanceAdapter(
        api_key=API_KEY,
        api_secret=SIGNING_KEY,
        quote_asset=QUOTE_ASSET,
    )

    # Then: direct construction is still testnet-safe by default.
    assert adapter.base_url == "https://testnet.binancefuture.com"


async def test_binance_futures_adapter_rejects_missing_quote_asset() -> None:
    # Given: Binance responds without the configured quote asset row.
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"asset": "BTC", "balance": "0.25"}])

    async with _client(handler) as client:
        adapter = BinanceFuturesBalanceAdapter(
            api_key=API_KEY,
            api_secret=SIGNING_KEY,
            quote_asset=QUOTE_ASSET,
            client=client,
            timestamp_ms=_fixed_timestamp_ms,
        )

        # When / Then: the adapter reports a typed response-shape failure.
        with pytest.raises(ExchangeError) as exc_info:
            await adapter.fetch_balance()
    assert exc_info.value.code is ExchangeErrorCode.EXCHANGE_RESPONSE_INVALID


async def test_binance_futures_adapter_maps_auth_http_error() -> None:
    # Given: Binance rejects the key or IP allowlist.
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"code": -2015, "msg": "Invalid API-key."})

    async with _client(handler) as client:
        adapter = BinanceFuturesBalanceAdapter(
            api_key=API_KEY,
            api_secret=SIGNING_KEY,
            quote_asset=QUOTE_ASSET,
            client=client,
            timestamp_ms=_fixed_timestamp_ms,
        )

        # When / Then: auth failures are machine-coded without leaking credentials.
        with pytest.raises(ExchangeError) as exc_info:
            await adapter.fetch_balance()
    assert exc_info.value.code is ExchangeErrorCode.EXCHANGE_AUTH_FAILED
    assert API_KEY not in exc_info.value.message
    assert SIGNING_KEY not in exc_info.value.message


def _fixed_timestamp_ms() -> int:
    return FIXED_TIMESTAMP_MS


def _signature(params: tuple[tuple[str, str], ...]) -> str:
    payload = urlencode(params)
    return hmac.new(SIGNING_KEY.encode(), payload.encode(), sha256).hexdigest()


def _client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.AsyncClient:
    transport = httpx.MockTransport(handler)
    return httpx.AsyncClient(transport=transport, base_url="https://fapi.binance.com")
