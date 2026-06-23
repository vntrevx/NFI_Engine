from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from nfi_engine.domain import PositionSide, TradeState
from nfi_engine.paper import BotState


@dataclass(frozen=True, slots=True)
class DashboardAction:
    code: str
    severity: str
    title: str
    detail: str
    target: str


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
class DashboardReadModels:
    equity_points: tuple[DashboardEquityPoint, ...] = ()
    price_points: tuple[DashboardPricePoint, ...] = ()
    open_positions: tuple[DashboardOpenPosition, ...] = ()
    recent_trades: tuple[DashboardRecentTrade, ...] = ()

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
    equity_points: tuple[DashboardEquityPoint, ...]
    price_points: tuple[DashboardPricePoint, ...]
    open_positions: tuple[DashboardOpenPosition, ...]
    recent_trades: tuple[DashboardRecentTrade, ...]
    recent_errors: tuple[DashboardError, ...]
