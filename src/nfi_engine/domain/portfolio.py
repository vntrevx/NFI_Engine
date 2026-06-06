from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime
    from decimal import Decimal

    from nfi_engine.domain.enums import (
        OrderState,
        PositionSide,
        SignalType,
        TradeState,
        TradingMode,
    )
    from nfi_engine.domain.pairs import TradingPair
    from nfi_engine.domain.primitives import (
        OrderId,
        Price,
        Quantity,
        SignalId,
        StakeAmount,
        TradeId,
    )
    from nfi_engine.domain.risk import Leverage, LiquidationBuffer


@dataclass(frozen=True, slots=True)
class Candle:
    pair: TradingPair
    opened_at: datetime
    open: Price
    high: Price
    low: Price
    close: Price
    volume: Quantity


@dataclass(frozen=True, slots=True)
class Signal:
    signal_id: SignalId
    pair: TradingPair
    trading_mode: TradingMode
    side: PositionSide
    signal_type: SignalType
    confidence: Decimal
    reason: str


@dataclass(frozen=True, slots=True)
class ExecutionReport:
    order_id: OrderId
    state: OrderState
    filled_quantity: Quantity
    average_price: Price | None
    reason: str | None


@dataclass(frozen=True, slots=True)
class Position:
    trade_id: TradeId
    pair: TradingPair
    side: PositionSide
    quantity: Quantity
    entry_price: Price
    leverage: Leverage
    liquidation_buffer: LiquidationBuffer
    state: TradeState


@dataclass(frozen=True, slots=True)
class AccountSnapshot:
    captured_at: datetime
    equity: StakeAmount
    available: StakeAmount
    positions: tuple[Position, ...]
