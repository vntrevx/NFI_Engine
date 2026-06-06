from __future__ import annotations

from decimal import Decimal
from typing import assert_never

from nfi_engine.domain import (
    ExecutionReport,
    OrderIntentDraft,
    OrderState,
    OrderType,
    Position,
    Price,
    Quantity,
    TimeInForce,
    TradeState,
    TradingMode,
    create_order_intent,
)
from nfi_engine.orders.models import OrderPlan, PositionUpdate
from nfi_engine.risk import AcceptedOrderQuote

ZERO: Decimal = Decimal(0)


def create_order_plan(
    *,
    quote: AcceptedOrderQuote,
    trading_mode: TradingMode,
    order_type: OrderType,
    time_in_force: TimeInForce,
    price: Price,
) -> OrderPlan:
    create_order_intent(
        OrderIntentDraft(
            pair=quote.pair,
            trading_mode=trading_mode,
            side=quote.side,
            order_type=order_type,
            leverage=quote.leverage,
            time_in_force=time_in_force,
        ),
    )
    notional = quote.stake * quote.leverage.value
    return OrderPlan(
        pair=quote.pair,
        side=quote.side,
        order_type=order_type,
        time_in_force=time_in_force,
        stake=quote.stake,
        quantity=Quantity(notional / price),
        leverage=quote.leverage,
        adjusted=quote.adjusted,
        reason=quote.reason,
    )


def apply_execution_report(*, position: Position, report: ExecutionReport) -> PositionUpdate:
    match report.state:
        case OrderState.FILLED:
            return _filled_position_update(position=position, report=report)
        case OrderState.PARTIALLY_FILLED:
            return _partially_filled_position_update(position=position, report=report)
        case OrderState.REJECTED:
            return _with_state(
                position=position,
                trade_state=TradeState.HALTED,
                order_state=report.state,
            )
        case OrderState.CREATED | OrderState.OPEN | OrderState.CANCELED:
            return _with_state(
                position=position,
                trade_state=position.state,
                order_state=report.state,
            )
        case unreachable:
            assert_never(unreachable)


def _filled_position_update(*, position: Position, report: ExecutionReport) -> PositionUpdate:
    remaining = max(position.quantity - report.filled_quantity, ZERO)
    if remaining == ZERO:
        closed = _replace_quantity(
            position=position,
            quantity=Quantity(ZERO),
            state=TradeState.CLOSED,
        )
        return PositionUpdate(
            position=closed,
            trade_state=TradeState.CLOSED,
            order_state=report.state,
        )
    updated = _replace_quantity(
        position=position,
        quantity=Quantity(remaining),
        state=TradeState.OPEN,
    )
    return PositionUpdate(position=updated, trade_state=TradeState.OPEN, order_state=report.state)


def _partially_filled_position_update(
    *,
    position: Position,
    report: ExecutionReport,
) -> PositionUpdate:
    remaining = max(position.quantity - report.filled_quantity, ZERO)
    updated = _replace_quantity(
        position=position,
        quantity=Quantity(remaining),
        state=TradeState.OPEN,
    )
    return PositionUpdate(position=updated, trade_state=TradeState.OPEN, order_state=report.state)


def _with_state(
    *,
    position: Position,
    trade_state: TradeState,
    order_state: OrderState,
) -> PositionUpdate:
    updated = _replace_quantity(position=position, quantity=position.quantity, state=trade_state)
    return PositionUpdate(position=updated, trade_state=trade_state, order_state=order_state)


def _replace_quantity(*, position: Position, quantity: Quantity, state: TradeState) -> Position:
    return Position(
        trade_id=position.trade_id,
        pair=position.pair,
        side=position.side,
        quantity=quantity,
        entry_price=position.entry_price,
        leverage=position.leverage,
        liquidation_buffer=position.liquidation_buffer,
        state=state,
    )
