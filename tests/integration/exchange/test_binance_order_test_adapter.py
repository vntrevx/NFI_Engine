from __future__ import annotations

import hmac
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from hashlib import sha256
from urllib.parse import urlencode

import httpx
import pytest

from nfi_engine.config.models import ExchangeSettings, RuntimeSettings
from nfi_engine.domain import (
    Leverage,
    OrderState,
    OrderType,
    PositionSide,
    Price,
    Quantity,
    TradingMode,
    TradingPair,
)
from nfi_engine.exchange.binance_order_test import BinanceFuturesOrderTestAdapter
from nfi_engine.exchange.errors import ExchangeError, ExchangeErrorCode
from nfi_engine.exchange.models import ExchangeOrderRequest

pytestmark = pytest.mark.anyio

FIXED_TIMESTAMP_MS = 1_700_000_000_000
API_KEY = "test-binance-key"
SIGNING_KEY = "test-binance-signing-key"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_binance_futures_order_test_posts_signed_testnet_request() -> None:
    # Given
    client = RecordingPostClient()
    adapter = BinanceFuturesOrderTestAdapter(
        api_key=API_KEY,
        api_secret=SIGNING_KEY,
        client=client,
        timestamp_ms=_fixed_timestamp_ms,
    )
    request = ExchangeOrderRequest(
        pair=TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
        side=PositionSide.SHORT,
        order_type=OrderType.LIMIT,
        quantity=Quantity(Decimal("0.25")),
        price=Price(Decimal(101)),
        leverage=Leverage.parse("3"),
    )

    # When
    order = await adapter.test_order(request)

    # Then
    assert order.state is OrderState.OPEN
    assert order.live_exchange is False
    assert order.pair == request.pair
    assert order.side is PositionSide.SHORT
    assert client.requests
    http_request = client.requests[0]
    assert http_request.method == "POST"
    assert http_request.url.host == "demo-fapi.binance.com"
    assert http_request.url.path == "/fapi/v1/order/test"
    assert http_request.headers["X-MBX-APIKEY"] == API_KEY
    assert http_request.url.params["symbol"] == "BTCUSDT"
    assert http_request.url.params["side"] == "SELL"
    assert http_request.url.params["type"] == "LIMIT"
    assert http_request.url.params["timeInForce"] == "GTC"
    assert http_request.url.params["quantity"] == "0.25"
    assert http_request.url.params["price"] == "101"
    assert http_request.url.params["recvWindow"] == "5000"
    assert http_request.url.params["timestamp"] == str(FIXED_TIMESTAMP_MS)
    assert http_request.url.params["signature"] == _signature(
        (
            ("symbol", "BTCUSDT"),
            ("side", "SELL"),
            ("type", "LIMIT"),
            ("timeInForce", "GTC"),
            ("quantity", "0.25"),
            ("price", "101"),
            ("recvWindow", "5000"),
            ("timestamp", str(FIXED_TIMESTAMP_MS)),
        ),
    )
    assert SIGNING_KEY not in str(http_request.url)


def test_binance_futures_order_test_uses_official_testnet_base_url_from_settings() -> None:
    # Given
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="binance",
            trading_mode=TradingMode.FUTURES,
            testnet=True,
            api_key=API_KEY,
            api_secret=SIGNING_KEY,
        ),
    )

    # When
    adapter = BinanceFuturesOrderTestAdapter.from_settings(settings=settings)

    # Then
    assert adapter.base_url == "https://demo-fapi.binance.com"


def test_binance_futures_order_test_refuses_non_testnet_config() -> None:
    # Given
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="binance",
            trading_mode=TradingMode.FUTURES,
            testnet=False,
            api_key=API_KEY,
            api_secret=SIGNING_KEY,
        ),
    )

    # When / Then
    with pytest.raises(ExchangeError) as exc_info:
        BinanceFuturesOrderTestAdapter.from_settings(settings=settings)
    assert exc_info.value.code is ExchangeErrorCode.LIVE_EXCHANGE_DISABLED_FOR_MILESTONE


def test_binance_futures_order_test_requires_limit_price() -> None:
    # Given
    adapter = BinanceFuturesOrderTestAdapter(api_key=API_KEY, api_secret=SIGNING_KEY)
    request = ExchangeOrderRequest(
        pair=TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
        side=PositionSide.LONG,
        order_type=OrderType.LIMIT,
        quantity=Quantity(Decimal("0.25")),
        price=None,
        leverage=Leverage.parse("3"),
    )

    # When / Then
    with pytest.raises(ExchangeError) as exc_info:
        adapter.signed_order_params(request=request, timestamp_ms=FIXED_TIMESTAMP_MS)
    assert exc_info.value.code is ExchangeErrorCode.ORDER_PAYLOAD_INVALID


def _fixed_timestamp_ms() -> int:
    return FIXED_TIMESTAMP_MS


def _signature(params: tuple[tuple[str, str], ...]) -> str:
    payload = urlencode(params)
    return hmac.new(SIGNING_KEY.encode(), payload.encode(), sha256).hexdigest()


@dataclass(frozen=True, slots=True)
class RecordingPostClient:
    requests: list[httpx.Request] = field(default_factory=list)

    async def post(
        self,
        url: str,
        *,
        params: tuple[tuple[str, str], ...],
        headers: Mapping[str, str],
    ) -> httpx.Response:
        request = httpx.Request(
            "POST",
            f"https://demo-fapi.binance.com{url}",
            params=params,
            headers=headers,
        )
        self.requests.append(request)
        return httpx.Response(200, json={})
