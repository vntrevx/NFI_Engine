from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal

from nfi_engine.dashboard.truth_models import DashboardAccountTruth
from nfi_engine.domain import PositionSide, TradeState
from nfi_engine.execution import ExecutionEventType, ExecutionState
from nfi_engine.paper import BotState


@dataclass(frozen=True, slots=True)
class DashboardAction:
    code: str
    severity: str
    title: str
    detail: str
    target: str


@dataclass(frozen=True, slots=True)
class DashboardExecutionSignal:
    code: str
    title: str
    status: str
    detail: str


@dataclass(frozen=True, slots=True)
class DashboardExecutionIntent:
    intent_id: str
    pair: str
    side: PositionSide
    state: ExecutionState
    requested_quantity: Decimal
    requested_price: Decimal | None
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class DashboardExecutionOrder:
    execution_order_id: str
    intent_id: str
    pair: str
    side: PositionSide
    state: ExecutionState
    requested_quantity: Decimal
    requested_price: Decimal | None
    filled_quantity: Decimal
    average_fill_price: Decimal | None
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class DashboardExecutionFill:
    execution_fill_id: str
    intent_id: str
    execution_order_id: str
    pair: str
    side: PositionSide
    quantity: Decimal
    price: Decimal
    fee_asset: str | None
    fee_amount: Decimal | None
    filled_at: datetime


@dataclass(frozen=True, slots=True)
class DashboardExecutionEvent:
    event_id: int | None
    intent_id: str
    event_type: ExecutionEventType
    state: ExecutionState
    message: str
    raw_status_code: str | None
    metadata_json: str
    occurred_at: datetime


@dataclass(frozen=True, slots=True)
class DashboardEquityPoint:
    at: datetime
    equity: Decimal
    available: Decimal


@dataclass(frozen=True, slots=True)
class DashboardPricePoint:
    pair: str
    at: datetime
    price: Decimal


@dataclass(frozen=True, slots=True)
class DashboardOpenPosition:
    position_id: str
    pair: str
    side: PositionSide
    quantity: Decimal
    entry_price: Decimal
    leverage: Decimal
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class DashboardRecentTrade:
    trade_id: str
    pair: str
    side: PositionSide
    state: TradeState
    opened_at: datetime
    closed_at: datetime | None
    profit: Decimal


@dataclass(frozen=True, slots=True)
class DashboardClosedTradeSummary:
    closed_trades: int
    wins: int
    losses: int
    profit: Decimal

    @classmethod
    def empty(cls) -> DashboardClosedTradeSummary:
        return cls(closed_trades=0, wins=0, losses=0, profit=Decimal(0))


@dataclass(frozen=True, slots=True)
class DashboardReadModels:
    equity_points: tuple[DashboardEquityPoint, ...] = ()
    price_points: tuple[DashboardPricePoint, ...] = ()
    open_positions: tuple[DashboardOpenPosition, ...] = ()
    recent_trades: tuple[DashboardRecentTrade, ...] = ()
    execution_intents: tuple[DashboardExecutionIntent, ...] = ()
    open_execution_orders: tuple[DashboardExecutionOrder, ...] = ()
    recent_execution_fills: tuple[DashboardExecutionFill, ...] = ()
    recent_execution_events: tuple[DashboardExecutionEvent, ...] = ()
    closed_trade_summary: DashboardClosedTradeSummary = field(
        default_factory=DashboardClosedTradeSummary.empty,
    )

    @classmethod
    def empty(cls) -> DashboardReadModels:
        return cls()


@dataclass(frozen=True, slots=True)
class DashboardReadinessCheck:
    code: str
    status: str
    message: str


@dataclass(frozen=True, slots=True)
class DashboardReadiness:
    profile: str
    blocked: bool
    checks: tuple[DashboardReadinessCheck, ...]


@dataclass(frozen=True, slots=True)
class DashboardPairlistSummary:
    total: int
    preview: tuple[str, ...]
    quote_asset: str


@dataclass(frozen=True, slots=True)
class DashboardError:
    at: datetime
    code: str
    safe_summary: str
    correlation_id: str


@dataclass(frozen=True, slots=True)
class DashboardSnapshot:
    generated_at: datetime
    bot_state: BotState
    trading_mode: str
    exchange: str
    actions: tuple[DashboardAction, ...]
    readiness: DashboardReadiness
    pairlist: DashboardPairlistSummary
    execution_signals: tuple[DashboardExecutionSignal, ...]
    account_truth: DashboardAccountTruth
    equity_points: tuple[DashboardEquityPoint, ...]
    price_points: tuple[DashboardPricePoint, ...]
    open_positions: tuple[DashboardOpenPosition, ...]
    recent_trades: tuple[DashboardRecentTrade, ...]
    closed_trade_summary: DashboardClosedTradeSummary
    recent_errors: tuple[DashboardError, ...]
    execution_intents: tuple[DashboardExecutionIntent, ...]
    open_execution_orders: tuple[DashboardExecutionOrder, ...]
    recent_execution_fills: tuple[DashboardExecutionFill, ...]
    recent_execution_events: tuple[DashboardExecutionEvent, ...]
