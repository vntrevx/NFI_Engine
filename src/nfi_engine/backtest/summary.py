from __future__ import annotations

from decimal import Decimal

from nfi_engine.backtest.models import (
    BacktestSummary,
    EquityPoint,
    SimulationSettings,
    TradeRecord,
)


def summarize_backtest(
    *,
    settings: SimulationSettings,
    final_balance: Decimal,
    trades: tuple[TradeRecord, ...],
    equity_curve: tuple[EquityPoint, ...],
    rejected_entries: int,
) -> BacktestSummary:
    total_profit = final_balance - settings.starting_balance
    return BacktestSummary(
        starting_balance=settings.starting_balance,
        final_balance=final_balance,
        total_profit=total_profit,
        total_profit_pct=_profit_pct(
            total_profit=total_profit,
            starting_balance=settings.starting_balance,
        ),
        total_trades=len(trades),
        winning_trades=sum(1 for trade in trades if trade.profit > Decimal(0)),
        losing_trades=sum(1 for trade in trades if trade.profit < Decimal(0)),
        rejected_entries=rejected_entries,
        max_drawdown=_max_drawdown(equity_curve),
    )


def _profit_pct(*, total_profit: Decimal, starting_balance: Decimal) -> Decimal:
    if starting_balance == Decimal(0):
        return Decimal(0)
    return total_profit / starting_balance


def _max_drawdown(equity_curve: tuple[EquityPoint, ...]) -> Decimal:
    peak: Decimal | None = None
    max_drawdown = Decimal(0)
    for point in equity_curve:
        if peak is None or point.equity > peak:
            peak = point.equity
        if peak > Decimal(0):
            drawdown = (peak - point.equity) / peak
            max_drawdown = max(max_drawdown, drawdown)
    return max_drawdown
