from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path

import pytest

from nfi_engine.config import load_runtime_settings
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
from nfi_engine.exchange import (
    ExchangeError,
    ExchangeErrorCode,
    ExchangeOrderRequest,
)
from nfi_engine.exchange.bybit import (
    BybitTestnetAdapter,
    CcxtBalancePayload,
    CcxtFundingPayload,
    CcxtOrderPayload,
)

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_bybit_adapter_refuses_non_testnet_config() -> None:
    # Given
    settings = load_runtime_settings(Path("tests/fixtures/config/bybit-live-denied.yaml"))

    # When
    with pytest.raises(ExchangeError) as exc_info:
        BybitTestnetAdapter.from_settings(settings=settings, client=FakeCcxtClient())

    # Then
    assert exc_info.value.code is ExchangeErrorCode.LIVE_EXCHANGE_DISABLED_FOR_MILESTONE


async def test_bybit_adapter_maps_order_to_ccxt_testnet_client() -> None:
    # Given
    settings = load_runtime_settings(Path("examples/futures-paper.yaml"))
    client = FakeCcxtClient()
    adapter = BybitTestnetAdapter.from_settings(settings=settings, client=client)
    request = ExchangeOrderRequest(
        pair=TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
        side=PositionSide.SHORT,
        order_type=OrderType.LIMIT,
        quantity=Quantity(Decimal("0.25")),
        price=Price(Decimal(101)),
        leverage=Leverage.parse("2"),
    )

    # When
    order = await adapter.create_order(request)

    # Then
    assert client.sandbox_mode is True
    assert client.created_orders == (("BTC/USDT:USDT", "limit", "sell", "0.25", "101"),)
    assert order.state is OrderState.FILLED
    assert order.live_exchange is False


async def test_bybit_adapter_executes_testnet_order_lifecycle() -> None:
    # Given
    settings = load_runtime_settings(Path("examples/futures-paper.yaml"))
    client = FakeCcxtClient(response_status="open", funding_rate=Decimal("0.0001"))
    adapter = BybitTestnetAdapter.from_settings(settings=settings, client=client)
    pair = TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
    request = ExchangeOrderRequest(
        pair=pair,
        side=PositionSide.LONG,
        order_type=OrderType.LIMIT,
        quantity=Quantity(Decimal("0.25")),
        price=Price(Decimal(99)),
        leverage=Leverage.parse("3"),
    )

    # When
    created = await adapter.create_order(request)
    fetched = await adapter.fetch_order(created.order_id, pair)
    canceled = await adapter.cancel_order(created.order_id, pair)
    leverage = await adapter.set_leverage(pair=pair, leverage=Leverage.parse("3"))
    funding = await adapter.fetch_funding_rate(pair)

    # Then
    assert client.sandbox_mode is True
    assert created.state is OrderState.OPEN
    assert fetched.state is OrderState.OPEN
    assert canceled.state is OrderState.CANCELED
    assert leverage == Leverage.parse("3")
    assert funding.supported is True
    assert funding.rate == Decimal("0.0001")
    assert created.live_exchange is False
    assert canceled.live_exchange is False


async def test_bybit_adapter_maps_partial_and_rejected_order_states() -> None:
    # Given
    settings = load_runtime_settings(Path("examples/futures-paper.yaml"))
    partial_client = FakeCcxtClient(response_status="partially_filled")
    rejected_client = FakeCcxtClient(response_status="rejected")
    pair = TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
    request = ExchangeOrderRequest(
        pair=pair,
        side=PositionSide.SHORT,
        order_type=OrderType.LIMIT,
        quantity=Quantity(Decimal("0.25")),
        price=Price(Decimal(101)),
        leverage=Leverage.parse("2"),
    )

    # When
    partial = await BybitTestnetAdapter.from_settings(
        settings=settings,
        client=partial_client,
    ).create_order(request)
    rejected = await BybitTestnetAdapter.from_settings(
        settings=settings,
        client=rejected_client,
    ).create_order(request)

    # Then
    assert partial.state is OrderState.PARTIALLY_FILLED
    assert rejected.state is OrderState.REJECTED
    assert partial.live_exchange is False
    assert rejected.live_exchange is False


async def test_bybit_adapter_fetches_quote_balance_read_only() -> None:
    # Given
    settings = load_runtime_settings(Path("examples/futures-paper.yaml"))
    client = FakeCcxtClient()
    adapter = BybitTestnetAdapter.from_settings(settings=settings, client=client)

    # When
    balance = await adapter.fetch_balance()

    # Then
    assert client.sandbox_mode is True
    assert balance.equity == Decimal("1234.5")
    assert balance.available == Decimal("1200.25")
    assert balance.positions == ()


async def test_bybit_adapter_rejects_unknown_ccxt_order_status() -> None:
    # Given
    settings = load_runtime_settings(Path("examples/futures-paper.yaml"))
    client = FakeCcxtClient(response_status="unknown-status")
    adapter = BybitTestnetAdapter.from_settings(settings=settings, client=client)
    request = ExchangeOrderRequest(
        pair=TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
        side=PositionSide.LONG,
        order_type=OrderType.LIMIT,
        quantity=Quantity(Decimal("0.25")),
        price=Price(Decimal(101)),
        leverage=Leverage.parse("2"),
    )

    # When / Then
    with pytest.raises(ExchangeError) as exc_info:
        await adapter.create_order(request)
    assert exc_info.value.code is ExchangeErrorCode.ORDER_PAYLOAD_INVALID


async def test_bybit_adapter_rejects_unknown_ccxt_order_side() -> None:
    # Given
    settings = load_runtime_settings(Path("examples/futures-paper.yaml"))
    client = FakeCcxtClient()
    client.orders["bad-side"] = CcxtOrderPayload(
        id="bad-side",
        symbol="BTC/USDT:USDT",
        side="hold",
        type="limit",
        status="open",
        amount="0.25",
        average=None,
    )
    adapter = BybitTestnetAdapter.from_settings(settings=settings, client=client)

    # When / Then
    with pytest.raises(ExchangeError) as exc_info:
        await adapter.fetch_order(
            "bad-side",
            TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
        )
    assert exc_info.value.code is ExchangeErrorCode.ORDER_PAYLOAD_INVALID


async def test_bybit_adapter_uses_unsupported_funding_fallback() -> None:
    # Given
    settings = load_runtime_settings(Path("examples/futures-paper.yaml"))
    adapter = BybitTestnetAdapter.from_settings(settings=settings, client=FakeCcxtClient())

    # When
    funding = await adapter.fetch_funding_rate(
        TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
    )

    # Then
    assert funding.supported is False
    assert funding.rate == Decimal(0)


@dataclass(slots=True)
class FakeCcxtClient:
    sandbox_mode: bool = False
    created_orders: tuple[tuple[str, str, str, str, str | None], ...] = ()
    checked_symbols: tuple[str, ...] = ()
    response_status: str = "closed"
    funding_rate: Decimal | None = None
    orders: dict[str, CcxtOrderPayload] = field(default_factory=dict)

    def set_sandbox_mode(self, enabled: bool) -> None:
        self.sandbox_mode = enabled

    async def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: str,
        price: str | None,
    ) -> CcxtOrderPayload:
        self.created_orders += ((symbol, order_type, side, amount, price),)
        payload = CcxtOrderPayload(
            id="fake-order-1",
            symbol=symbol,
            side=side,
            type=order_type,
            status=self.response_status,
            amount=amount,
            average="100",
        )
        self.orders[payload["id"]] = payload
        return payload

    async def cancel_order(self, order_id: str, symbol: str) -> CcxtOrderPayload:
        self.checked_symbols += (symbol,)
        payload = self.orders[order_id]
        payload["status"] = "canceled"
        return payload

    async def fetch_order(self, order_id: str, symbol: str) -> CcxtOrderPayload:
        self.checked_symbols += (symbol,)
        return self.orders[order_id]

    async def fetch_funding_rate(self, symbol: str) -> CcxtFundingPayload:
        if self.funding_rate is None:
            raise NotImplementedError(symbol)
        return CcxtFundingPayload(symbol=symbol, fundingRate=str(self.funding_rate))

    async def set_leverage(self, leverage: int, symbol: str) -> CcxtOrderPayload:
        return CcxtOrderPayload(
            id="leverage",
            symbol=symbol,
            side="buy",
            type="market",
            status="closed",
            amount=str(leverage),
            average=None,
        )

    async def fetch_balance(self) -> CcxtBalancePayload:
        return CcxtBalancePayload(
            total={"USDT": "1234.5"},
            free={"USDT": "1200.25"},
        )
