from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Final

from nfi_engine.dashboard.models import (
    DashboardClosedTradeSummary,
    DashboardEquityPoint,
    DashboardOpenPosition,
    DashboardReadModels,
    DashboardRecentTrade,
)
from nfi_engine.dashboard.summary import DashboardRiskPressure, summarize_dashboard_read_models
from nfi_engine.domain import PositionSide, TradeState

NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)


def test_operator_summary_calculates_portfolio_exposure() -> None:
    read_models = DashboardReadModels(
        equity_points=(DashboardEquityPoint(at=NOW, equity=Decimal(1000), available=Decimal(750)),),
        open_positions=(
            _position("position-1", quantity=Decimal("0.10"), price=Decimal(1000), leverage=3),
            _position("position-2", quantity=Decimal("0.20"), price=Decimal(500), leverage=2),
        ),
        recent_trades=(
            DashboardRecentTrade(
                trade_id="trade-1",
                pair="BTC/USDT",
                side=PositionSide.LONG,
                state=TradeState.CLOSED,
                opened_at=NOW,
                closed_at=NOW,
                profit=Decimal("7.25"),
            ),
        ),
    )

    summary = summarize_dashboard_read_models(read_models)

    assert summary.open_trades == 2
    assert summary.closed_trades == 1
    assert summary.session_profit == Decimal("7.25")
    assert summary.account_equity == Decimal(1000)
    assert summary.account_available == Decimal(750)
    assert summary.gross_exposure == Decimal("500.00")
    assert summary.exposure_pct == Decimal("50.00")
    assert summary.average_leverage == Decimal("2.5")
    assert summary.risk_pressure is DashboardRiskPressure.BALANCED


def test_operator_summary_marks_exposure_without_equity_as_elevated() -> None:
    read_models = DashboardReadModels(
        open_positions=(
            _position("position-1", quantity=Decimal("0.10"), price=Decimal(1000), leverage=3),
        ),
    )

    summary = summarize_dashboard_read_models(read_models)

    assert summary.account_equity == Decimal(0)
    assert summary.exposure_pct == Decimal(0)
    assert summary.risk_pressure is DashboardRiskPressure.ELEVATED


def test_operator_summary_prefers_closed_trade_summary_over_recent_window() -> None:
    read_models = DashboardReadModels(
        closed_trade_summary=DashboardClosedTradeSummary(
            closed_trades=3,
            wins=1,
            losses=2,
            profit=Decimal("-4.50"),
        ),
        recent_trades=(
            DashboardRecentTrade(
                trade_id="recent-win",
                pair="BTC/USDT",
                side=PositionSide.LONG,
                state=TradeState.CLOSED,
                opened_at=NOW,
                closed_at=NOW,
                profit=Decimal("99.00"),
            ),
        ),
    )

    summary = summarize_dashboard_read_models(read_models)

    assert summary.closed_trades == 3
    assert summary.session_profit == Decimal("-4.50")


def test_operator_summary_marks_empty_runtime_as_idle() -> None:
    summary = summarize_dashboard_read_models(DashboardReadModels.empty())

    assert summary.gross_exposure == Decimal(0)
    assert summary.average_leverage == Decimal(0)
    assert summary.risk_pressure is DashboardRiskPressure.IDLE


def _position(
    position_id: str,
    *,
    quantity: Decimal,
    price: Decimal,
    leverage: int,
) -> DashboardOpenPosition:
    return DashboardOpenPosition(
        position_id=position_id,
        pair="BTC/USDT",
        side=PositionSide.LONG,
        quantity=quantity,
        entry_price=price,
        leverage=Decimal(leverage),
        updated_at=NOW,
    )
