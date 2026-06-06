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
from nfi_engine.exchange.bybit import BybitTestnetAdapter, CcxtFundingPayload, CcxtOrderPayload

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
            status="closed",
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
        raise NotImplementedError(symbol)

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
