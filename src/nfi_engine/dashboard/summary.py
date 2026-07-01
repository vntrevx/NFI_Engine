from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum, unique
from typing import Final

from nfi_engine.dashboard.models import DashboardReadModels
from nfi_engine.domain import TradeState

PERCENT_MULTIPLIER: Final = Decimal(100)
ELEVATED_EXPOSURE_PCT: Final = Decimal(100)


@unique
class DashboardRiskPressure(StrEnum):
    IDLE = "idle"
    BALANCED = "balanced"
    ELEVATED = "elevated"


@dataclass(frozen=True, slots=True)
class DashboardOperatorSummary:
    open_trades: int
    closed_trades: int
    session_profit: Decimal
    account_equity: Decimal
    account_available: Decimal
    gross_exposure: Decimal
    exposure_pct: Decimal
    average_leverage: Decimal
    risk_pressure: DashboardRiskPressure
    trade_ids: tuple[str, ...]


def summarize_dashboard_read_models(
    read_models: DashboardReadModels,
) -> DashboardOperatorSummary:
    account_equity, account_available = _latest_account_values(read_models)
    gross_exposure = _gross_exposure(read_models)
    exposure_pct = _exposure_pct(gross_exposure=gross_exposure, account_equity=account_equity)
    closed_trades, session_profit = _closed_trade_totals(read_models)
    return DashboardOperatorSummary(
        open_trades=len(read_models.open_positions),
        closed_trades=closed_trades,
        session_profit=session_profit,
        account_equity=account_equity,
        account_available=account_available,
        gross_exposure=gross_exposure,
        exposure_pct=exposure_pct,
        average_leverage=_average_leverage(read_models),
        risk_pressure=_risk_pressure(
            gross_exposure=gross_exposure,
            account_equity=account_equity,
            exposure_pct=exposure_pct,
        ),
        trade_ids=tuple(trade.trade_id for trade in read_models.recent_trades),
    )


def _closed_trade_totals(read_models: DashboardReadModels) -> tuple[int, Decimal]:
    summary = read_models.closed_trade_summary
    if summary.closed_trades > 0 or summary.profit != Decimal(0):
        return summary.closed_trades, summary.profit
    closed_recent = tuple(
        trade for trade in read_models.recent_trades if trade.state is TradeState.CLOSED
    )
    return len(closed_recent), sum((trade.profit for trade in closed_recent), Decimal(0))


def _latest_account_values(read_models: DashboardReadModels) -> tuple[Decimal, Decimal]:
    if read_models.equity_points == ():
        return Decimal(0), Decimal(0)
    point = read_models.equity_points[-1]
    return point.equity, point.available


def _gross_exposure(read_models: DashboardReadModels) -> Decimal:
    return sum(
        (
            abs(position.quantity) * position.entry_price * position.leverage
            for position in read_models.open_positions
        ),
        Decimal(0),
    )


def _average_leverage(read_models: DashboardReadModels) -> Decimal:
    if read_models.open_positions == ():
        return Decimal(0)
    return sum(
        (position.leverage for position in read_models.open_positions),
        Decimal(0),
    ) / Decimal(len(read_models.open_positions))


def _exposure_pct(*, gross_exposure: Decimal, account_equity: Decimal) -> Decimal:
    if account_equity <= Decimal(0):
        return Decimal(0)
    return (gross_exposure / account_equity) * PERCENT_MULTIPLIER


def _risk_pressure(
    *,
    gross_exposure: Decimal,
    account_equity: Decimal,
    exposure_pct: Decimal,
) -> DashboardRiskPressure:
    if gross_exposure <= Decimal(0):
        return DashboardRiskPressure.IDLE
    if account_equity <= Decimal(0):
        return DashboardRiskPressure.ELEVATED
    if exposure_pct <= ELEVATED_EXPOSURE_PCT:
        return DashboardRiskPressure.BALANCED
    return DashboardRiskPressure.ELEVATED
