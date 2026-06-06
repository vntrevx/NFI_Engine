from __future__ import annotations

from dataclasses import dataclass

from nfi_engine.domain import (
    Leverage,
    OrderState,
    OrderType,
    Position,
    PositionSide,
    Quantity,
    StakeAmount,
    TimeInForce,
    TradeState,
    TradingPair,
)


@dataclass(frozen=True, slots=True)
class OrderPlan:
    pair: TradingPair
    side: PositionSide
    order_type: OrderType
    time_in_force: TimeInForce
    stake: StakeAmount
    quantity: Quantity
    leverage: Leverage
    adjusted: bool
    reason: str | None


@dataclass(frozen=True, slots=True)
class PositionUpdate:
    position: Position
    trade_state: TradeState
    order_state: OrderState
