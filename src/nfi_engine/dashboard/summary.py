from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from nfi_engine.dashboard.models import DashboardReadModels
from nfi_engine.domain import TradeState


@dataclass(frozen=True, slots=True)
class DashboardOperatorSummary:
    open_trades: int
    closed_trades: int
    session_profit: Decimal
    trade_ids: tuple[str, ...]


def summarize_dashboard_read_models(
    read_models: DashboardReadModels,
) -> DashboardOperatorSummary:
    return DashboardOperatorSummary(
        open_trades=len(read_models.open_positions),
        closed_trades=sum(
            1 for trade in read_models.recent_trades if trade.state is TradeState.CLOSED
        ),
        session_profit=sum((trade.profit for trade in read_models.recent_trades), Decimal(0)),
        trade_ids=tuple(trade.trade_id for trade in read_models.recent_trades),
    )
