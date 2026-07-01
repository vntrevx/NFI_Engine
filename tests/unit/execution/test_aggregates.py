from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Final

from nfi_engine.domain import PositionSide
from nfi_engine.execution.aggregates import (
    ExecutionAggregateFill,
    ExecutionAggregateInput,
    ExecutionAggregateOrder,
    ExecutionAggregatePosition,
    ExecutionAggregatePrice,
    ExecutionAggregateTrade,
    calculate_execution_aggregate,
)

NOW: Final = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)


def test_execution_aggregate_calculates_decimal_pnl_fees_and_partial_fills() -> None:
    summary = calculate_execution_aggregate(
        ExecutionAggregateInput(
            now=NOW,
            stale_after=timedelta(minutes=1),
            positions=(
                ExecutionAggregatePosition(
                    pair="BTC/USDT",
                    side=PositionSide.LONG,
                    quantity=Decimal(2),
                    entry_price=Decimal(100),
                    leverage=Decimal(3),
                ),
            ),
            prices=(
                ExecutionAggregatePrice(
                    pair="BTC/USDT",
                    price=Decimal(110),
                    captured_at=NOW,
                ),
            ),
            closed_trades=(
                ExecutionAggregateTrade(profit=Decimal(10)),
                ExecutionAggregateTrade(profit=Decimal(-4)),
                ExecutionAggregateTrade(profit=Decimal(0)),
            ),
            orders=(
                ExecutionAggregateOrder(
                    requested_quantity=Decimal(2),
                    filled_quantity=Decimal(1),
                ),
            ),
            fills=(
                ExecutionAggregateFill(fee_asset="USDT", fee_amount=Decimal("0.25")),
                ExecutionAggregateFill(fee_asset="BNB", fee_amount=Decimal("0.01")),
            ),
        ),
    )

    assert summary.open_profit == Decimal(60)
    assert summary.closed_profit == Decimal(6)
    assert summary.wins == 1
    assert summary.losses == 1
    assert summary.breakeven == 1
    assert summary.open_notional == Decimal(220)
    assert summary.account_exposure == Decimal(660)
    assert summary.realized_quote_fees == Decimal("0.25")
    assert summary.partial_fills == 1
    assert summary.confident_open_values is True
    assert summary.stale_data is False
    assert summary.stale_pairs == ()


def test_execution_aggregate_blocks_open_values_for_empty_or_stale_prices() -> None:
    empty = calculate_execution_aggregate(
        ExecutionAggregateInput(now=NOW, stale_after=timedelta(minutes=1)),
    )

    assert empty.open_profit == Decimal(0)
    assert empty.open_notional == Decimal(0)
    assert empty.account_exposure == Decimal(0)
    assert empty.confident_open_values is True
    assert empty.stale_data is False

    stale = calculate_execution_aggregate(
        ExecutionAggregateInput(
            now=NOW,
            stale_after=timedelta(minutes=1),
            positions=(
                ExecutionAggregatePosition(
                    pair="BTC/USDT",
                    side=PositionSide.LONG,
                    quantity=Decimal(1),
                    entry_price=Decimal(100),
                    leverage=Decimal(3),
                ),
                ExecutionAggregatePosition(
                    pair="ETH/USDT",
                    side=PositionSide.SHORT,
                    quantity=Decimal(1),
                    entry_price=Decimal(100),
                    leverage=Decimal(2),
                ),
            ),
            prices=(
                ExecutionAggregatePrice(
                    pair="ETH/USDT",
                    price=Decimal(95),
                    captured_at=NOW - timedelta(minutes=5),
                ),
            ),
        ),
    )

    assert stale.open_profit is None
    assert stale.open_notional is None
    assert stale.account_exposure is None
    assert stale.confident_open_values is False
    assert stale.stale_data is True
    assert stale.stale_pairs == ("BTC/USDT", "ETH/USDT")
