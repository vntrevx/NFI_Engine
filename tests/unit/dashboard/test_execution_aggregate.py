from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Final

from nfi_engine.dashboard.execution_aggregate import summarize_dashboard_execution_aggregate
from nfi_engine.dashboard.models import (
    DashboardExecutionFill,
    DashboardExecutionOrder,
    DashboardOpenPosition,
    DashboardPricePoint,
    DashboardReadModels,
    DashboardRecentTrade,
)
from nfi_engine.domain import PositionSide, TradeState
from nfi_engine.execution import ExecutionState

NOW: Final = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)


def test_dashboard_execution_aggregate_uses_backend_decimal_math() -> None:
    summary = summarize_dashboard_execution_aggregate(
        DashboardReadModels(
            price_points=(DashboardPricePoint(pair="BTC/USDT", at=NOW, price=Decimal(110)),),
            open_positions=(
                DashboardOpenPosition(
                    position_id="position-1",
                    pair="BTC/USDT",
                    side=PositionSide.LONG,
                    quantity=Decimal(2),
                    entry_price=Decimal(100),
                    leverage=Decimal(3),
                    updated_at=NOW,
                ),
            ),
            recent_trades=(
                DashboardRecentTrade(
                    trade_id="trade-1",
                    pair="BTC/USDT",
                    side=PositionSide.LONG,
                    state=TradeState.CLOSED,
                    opened_at=NOW - timedelta(minutes=10),
                    closed_at=NOW,
                    profit=Decimal(12),
                ),
            ),
            open_execution_orders=(
                DashboardExecutionOrder(
                    execution_order_id="order-1",
                    intent_id="intent-1",
                    pair="BTC/USDT",
                    side=PositionSide.LONG,
                    state=ExecutionState.PARTIALLY_FILLED,
                    requested_quantity=Decimal(2),
                    requested_price=Decimal(100),
                    filled_quantity=Decimal(1),
                    average_fill_price=Decimal(100),
                    updated_at=NOW,
                ),
            ),
            recent_execution_fills=(
                DashboardExecutionFill(
                    execution_fill_id="fill-1",
                    intent_id="intent-1",
                    execution_order_id="order-1",
                    pair="BTC/USDT",
                    side=PositionSide.LONG,
                    quantity=Decimal(1),
                    price=Decimal(100),
                    fee_asset="USDT",
                    fee_amount=Decimal("0.15"),
                    filled_at=NOW,
                ),
            ),
        ),
        now=NOW,
        stale_after=timedelta(minutes=1),
    )

    assert summary.open_profit == Decimal(60)
    assert summary.closed_profit == Decimal(12)
    assert summary.wins == 1
    assert summary.open_notional == Decimal(220)
    assert summary.account_exposure == Decimal(660)
    assert summary.realized_quote_fees == Decimal("0.15")
    assert summary.partial_fills == 1
    assert summary.confident_open_values is True
