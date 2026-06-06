from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Final

from nfi_engine.domain import (
    ExecutionReport,
    Leverage,
    LiquidationBuffer,
    OrderId,
    OrderState,
    OrderType,
    Position,
    PositionSide,
    Price,
    Quantity,
    StakeAmount,
    TimeInForce,
    TradeId,
    TradeState,
    TradingMode,
    TradingPair,
)
from nfi_engine.orders import (
    OrderPlan,
    PositionUpdate,
    apply_execution_report,
    create_order_plan,
)
from nfi_engine.risk import AcceptedOrderQuote

NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)


def test_create_order_plan_converts_quote_to_order_intent_and_quantity() -> None:
    # Given
    quote = AcceptedOrderQuote(
        pair=TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
        side=PositionSide.SHORT,
        stake=StakeAmount(Decimal(100)),
        leverage=Leverage.parse("3"),
        adjusted=True,
        reason="LEVERAGE_CAPPED",
    )

    # When
    plan = create_order_plan(
        quote=quote,
        trading_mode=TradingMode.FUTURES,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.GTC,
        price=Price(Decimal(50)),
    )

    # Then
    assert plan == OrderPlan(
        pair=TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
        side=PositionSide.SHORT,
        order_type=OrderType.MARKET,
        time_in_force=TimeInForce.GTC,
        stake=StakeAmount(Decimal(100)),
        quantity=Quantity(Decimal(6)),
        leverage=Leverage.parse("3"),
        adjusted=True,
        reason="LEVERAGE_CAPPED",
    )


def test_apply_execution_report_closes_position_on_full_fill() -> None:
    # Given
    position = Position(
        trade_id=TradeId("trade-1"),
        pair=TradingPair.parse("BTC/USDT", TradingMode.SPOT),
        side=PositionSide.LONG,
        quantity=Quantity(Decimal(2)),
        entry_price=Price(Decimal(100)),
        leverage=Leverage.one(),
        liquidation_buffer=LiquidationBuffer.parse("0.05"),
        state=TradeState.OPEN,
    )
    report = ExecutionReport(
        order_id=OrderId("order-1"),
        state=OrderState.FILLED,
        filled_quantity=Quantity(Decimal(2)),
        average_price=Price(Decimal(110)),
        reason=None,
    )

    # When
    update = apply_execution_report(position=position, report=report)

    # Then
    assert update == PositionUpdate(
        position=Position(
            trade_id=TradeId("trade-1"),
            pair=TradingPair.parse("BTC/USDT", TradingMode.SPOT),
            side=PositionSide.LONG,
            quantity=Quantity(Decimal(0)),
            entry_price=Price(Decimal(100)),
            leverage=Leverage.one(),
            liquidation_buffer=LiquidationBuffer.parse("0.05"),
            state=TradeState.CLOSED,
        ),
        trade_state=TradeState.CLOSED,
        order_state=OrderState.FILLED,
    )
