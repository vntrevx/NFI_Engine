from __future__ import annotations

from datetime import datetime, timedelta
from decimal import Decimal

from nfi_engine.dashboard.models import DashboardReadModels
from nfi_engine.domain import TradeState
from nfi_engine.execution.aggregates import (
    ExecutionAggregateClosedTotals,
    ExecutionAggregateFill,
    ExecutionAggregateInput,
    ExecutionAggregateOrder,
    ExecutionAggregatePosition,
    ExecutionAggregatePrice,
    ExecutionAggregateSummary,
    ExecutionAggregateTrade,
    calculate_execution_aggregate,
)

ZERO = Decimal(0)


def summarize_dashboard_execution_aggregate(
    read_models: DashboardReadModels,
    *,
    now: datetime,
    stale_after: timedelta,
) -> ExecutionAggregateSummary:
    return calculate_execution_aggregate(
        ExecutionAggregateInput(
            now=now,
            stale_after=stale_after,
            positions=tuple(
                ExecutionAggregatePosition(
                    pair=position.pair,
                    side=position.side,
                    quantity=position.quantity,
                    entry_price=position.entry_price,
                    leverage=position.leverage,
                )
                for position in read_models.open_positions
            ),
            prices=tuple(
                ExecutionAggregatePrice(
                    pair=point.pair,
                    price=point.price,
                    captured_at=point.at,
                )
                for point in read_models.price_points
            ),
            closed_trades=tuple(
                ExecutionAggregateTrade(profit=trade.profit)
                for trade in read_models.recent_trades
                if trade.state is TradeState.CLOSED
            ),
            closed_totals=_closed_totals(read_models),
            orders=tuple(
                ExecutionAggregateOrder(
                    requested_quantity=order.requested_quantity,
                    filled_quantity=order.filled_quantity,
                )
                for order in read_models.open_execution_orders
            ),
            fills=tuple(
                ExecutionAggregateFill(
                    fee_asset=fill.fee_asset,
                    fee_amount=fill.fee_amount,
                )
                for fill in read_models.recent_execution_fills
            ),
        ),
    )


def _closed_totals(read_models: DashboardReadModels) -> ExecutionAggregateClosedTotals | None:
    summary = read_models.closed_trade_summary
    if summary.closed_trades <= 0 and summary.profit == ZERO:
        return None
    return ExecutionAggregateClosedTotals(
        profit=summary.profit,
        wins=summary.wins,
        losses=summary.losses,
        breakeven=max(0, summary.closed_trades - summary.wins - summary.losses),
    )
