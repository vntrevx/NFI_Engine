from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from nfi_engine.domain import OrderState, OrderType, PositionSide, TradeState


@dataclass(frozen=True, slots=True)
class TradeRecord:
    trade_id: str
    pair: str
    side: PositionSide
    state: TradeState
    opened_at: datetime
    closed_at: datetime | None
    entry_price: Decimal
    exit_price: Decimal | None
    quantity: Decimal
    leverage: Decimal
    profit: Decimal


@dataclass(frozen=True, slots=True)
class OrderRecord:
    order_id: str
    trade_id: str
    pair: str
    side: PositionSide
    order_type: OrderType
    state: OrderState
    price: Decimal
    quantity: Decimal
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PositionRecord:
    position_id: str
    trade_id: str
    pair: str
    side: PositionSide
    state: TradeState
    quantity: Decimal
    entry_price: Decimal
    leverage: Decimal
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class LockRecord:
    name: str
    owner: str
    acquired_at: datetime
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class EquitySnapshotRecord:
    captured_at: datetime
    equity: Decimal
    available: Decimal


@dataclass(frozen=True, slots=True)
class StrategyCustomDataRecord:
    strategy_name: str
    key: str
    value_json: str
    updated_at: datetime
