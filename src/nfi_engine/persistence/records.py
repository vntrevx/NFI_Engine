from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from nfi_engine.domain import OrderState, OrderType, PositionSide, TradeState
from nfi_engine.execution import ExecutionEventType, ExecutionState


@dataclass(frozen=True, slots=True)
class TradeAggregateRecord:
    closed_trades: int
    wins: int
    losses: int
    profit: Decimal


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


@dataclass(frozen=True, slots=True)
class ExecutionIntentRecord:
    intent_id: str
    idempotency_key: str
    client_order_id: str
    pair: str
    side: PositionSide
    order_type: OrderType
    requested_quantity: Decimal
    requested_price: Decimal | None
    state: ExecutionState
    raw_status_code: str | None
    metadata_json: str
    created_at: datetime
    updated_at: datetime
    exchange_created_at: datetime | None
    exchange_updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class ExecutionOrderRecord:
    execution_order_id: str
    intent_id: str
    client_order_id: str
    exchange_order_id: str | None
    pair: str
    side: PositionSide
    order_type: OrderType
    requested_quantity: Decimal
    requested_price: Decimal | None
    filled_quantity: Decimal
    average_fill_price: Decimal | None
    state: ExecutionState
    raw_status_code: str | None
    metadata_json: str
    created_at: datetime
    updated_at: datetime
    exchange_created_at: datetime | None
    exchange_updated_at: datetime | None


@dataclass(frozen=True, slots=True)
class ExecutionFillRecord:
    execution_fill_id: str
    intent_id: str
    execution_order_id: str
    exchange_order_id: str | None
    pair: str
    side: PositionSide
    quantity: Decimal
    price: Decimal
    fee_asset: str | None
    fee_amount: Decimal | None
    metadata_json: str
    filled_at: datetime


@dataclass(frozen=True, slots=True)
class ExecutionEventRecord:
    event_id: int | None
    intent_id: str
    event_type: ExecutionEventType
    state: ExecutionState
    message: str
    raw_status_code: str | None
    metadata_json: str
    occurred_at: datetime
