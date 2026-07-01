from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class DashboardBalanceTruth:
    equity: Decimal
    available: Decimal
    synced_at: datetime | None
    stale: bool


@dataclass(frozen=True, slots=True)
class DashboardPnlTruth:
    open_profit: Decimal | None
    closed_profit: Decimal
    wins: int
    losses: int
    breakeven: int
    stale_data: bool
    stale_pairs: tuple[str, ...]
    confident_open_values: bool


@dataclass(frozen=True, slots=True)
class DashboardExposureTruth:
    open_notional: Decimal | None
    account_exposure: Decimal | None
    exposure_pct: Decimal | None
    realized_quote_fees: Decimal
    partial_fills: int


@dataclass(frozen=True, slots=True)
class DashboardReconciliationTruth:
    status: str
    trading_halted: bool
    mismatch_count: int
    issue_codes: tuple[str, ...]
    checked_at: datetime | None


@dataclass(frozen=True, slots=True)
class DashboardAccountTruth:
    balance: DashboardBalanceTruth
    pnl: DashboardPnlTruth
    exposure: DashboardExposureTruth
    reconciliation: DashboardReconciliationTruth
