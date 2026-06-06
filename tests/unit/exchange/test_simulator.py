from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Final

import pytest

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
    ExchangeOrderRequest,
    Tick,
    load_tick_fixture,
)
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator

pytestmark = pytest.mark.anyio

NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_simulator_fills_market_order_from_tick_fixture() -> None:
    # Given
    ticks = load_tick_fixture(Path("tests/fixtures/ticks/btc_usdt_spot.jsonl"), TradingMode.SPOT)
    simulator = DeterministicExchangeSimulator(ticks=ticks)
    request = ExchangeOrderRequest(
        pair=TradingPair.parse("BTC/USDT", TradingMode.SPOT),
        side=PositionSide.LONG,
        order_type=OrderType.MARKET,
        quantity=Quantity(Decimal("0.5")),
        price=None,
        leverage=Leverage.one(),
    )

    # When
    order = await simulator.create_order(request)

    # Then
    assert order.state is OrderState.FILLED
    assert order.filled_price == Price(Decimal(100))
    assert order.live_exchange is False


async def test_simulator_fills_limit_orders_deterministically() -> None:
    # Given
    simulator = DeterministicExchangeSimulator(
        ticks=(
            Tick(
                pair=TradingPair.parse("BTC/USDT", TradingMode.SPOT),
                price=Price(Decimal(100)),
                at=NOW,
            ),
        ),
    )
    request = ExchangeOrderRequest(
        pair=TradingPair.parse("BTC/USDT", TradingMode.SPOT),
        side=PositionSide.LONG,
        order_type=OrderType.LIMIT,
        quantity=Quantity(Decimal("0.5")),
        price=Price(Decimal(101)),
        leverage=Leverage.one(),
    )

    # When
    order = await simulator.create_order(request)

    # Then
    assert order.state is OrderState.FILLED
    assert order.filled_price == Price(Decimal(100))


async def test_simulator_handles_futures_leverage_and_funding_fallback() -> None:
    # Given
    pair = TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
    simulator = DeterministicExchangeSimulator(
        ticks=(Tick(pair=pair, price=Price(Decimal(100)), at=NOW),),
    )

    # When
    leverage = await simulator.set_leverage(pair=pair, leverage=Leverage.parse("3"))
    funding = await simulator.fetch_funding_rate(pair)

    # Then
    assert leverage == Leverage.parse("3")
    assert funding.supported is False
    assert funding.rate == Decimal(0)
