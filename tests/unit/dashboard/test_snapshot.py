from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Final

from nfi_engine.api.dashboard_models import DashboardSnapshotResponse
from nfi_engine.api.models import LogEntryResponse
from nfi_engine.config import LogLevel
from nfi_engine.config.models import RuntimeSettings
from nfi_engine.dashboard.models import (
    DashboardEquityPoint,
    DashboardOpenPosition,
    DashboardPricePoint,
    DashboardReadModels,
    DashboardRecentTrade,
)
from nfi_engine.dashboard.service import build_dashboard_snapshot
from nfi_engine.domain import PositionSide, TradeState
from nfi_engine.paper import BotState
from nfi_engine.preflight.models import (
    PreflightCheck,
    PreflightCode,
    PreflightReport,
    PreflightStatus,
)

NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)


def test_dashboard_snapshot_serializes_chart_ready_fixture_data() -> None:
    # Given: bounded read models with deterministic Decimal and datetime values.
    read_models = DashboardReadModels(
        equity_points=(
            DashboardEquityPoint(at=NOW, equity=Decimal("1000.10"), available=Decimal("990.05")),
        ),
        price_points=(DashboardPricePoint(pair="BTC/USDT", at=NOW, price=Decimal("101.25")),),
        open_positions=(
            DashboardOpenPosition(
                position_id="position-1",
                pair="BTC/USDT",
                side=PositionSide.LONG,
                quantity=Decimal("0.10"),
                entry_price=Decimal("100.00"),
                leverage=Decimal(2),
                updated_at=NOW,
            ),
        ),
        recent_trades=(
            DashboardRecentTrade(
                trade_id="trade-1",
                pair="BTC/USDT",
                side=PositionSide.LONG,
                state=TradeState.CLOSED,
                opened_at=NOW,
                closed_at=NOW,
                profit=Decimal("1.23"),
            ),
        ),
    )
    report = PreflightReport(
        profile="paper",
        blocked=True,
        checks=(
            PreflightCheck(
                code=PreflightCode.CONFIG_VALID,
                status=PreflightStatus.PASS,
                message="valid",
            ),
        ),
    )

    # When: a dashboard snapshot is built and converted to the API contract.
    snapshot = build_dashboard_snapshot(
        settings=RuntimeSettings(),
        bot_state=BotState.RUNNING,
        readiness=report,
        logs=(_log(LogLevel.ERROR, "CONFIG_VALIDATION_ERROR"), _log(LogLevel.INFO, "API_STARTED")),
        read_models=read_models,
    )
    payload = DashboardSnapshotResponse.from_snapshot(snapshot).model_dump(mode="json")

    # Then: chart arrays and user-visible status are deterministic.
    assert payload["bot_state"] == "running"
    assert payload["readiness"]["blocked"] is True
    assert payload["readiness"]["checks"][0]["code"] == "CONFIG_VALID"
    assert payload["equity_points"][0]["at"] == "2026-01-01T00:00:00Z"
    assert payload["equity_points"][0]["equity"] == "1000.10"
    assert payload["price_points"][0]["price"] == "101.25"
    assert payload["open_positions"][0]["leverage"] == "2"
    assert payload["recent_trades"][0]["profit"] == "1.23"
    assert payload["recent_errors"][0]["code"] == "CONFIG_VALIDATION_ERROR"


def test_dashboard_snapshot_returns_valid_empty_arrays_when_datasets_are_empty() -> None:
    # Given: a fresh local runtime with no persisted chart or trade data.
    report = PreflightReport(profile="paper", blocked=False, checks=())

    # When: the snapshot is built from empty read models.
    snapshot = build_dashboard_snapshot(
        settings=RuntimeSettings(),
        bot_state=BotState.STOPPED,
        readiness=report,
        logs=(),
        read_models=DashboardReadModels.empty(),
    )
    payload = DashboardSnapshotResponse.from_snapshot(snapshot).model_dump(mode="json")

    # Then: empty collections stay arrays and pairlist still summarizes configuration.
    assert payload["bot_state"] == "stopped"
    assert payload["readiness"]["blocked"] is False
    assert payload["equity_points"] == []
    assert payload["price_points"] == []
    assert payload["open_positions"] == []
    assert payload["recent_trades"] == []
    assert payload["recent_errors"] == []
    assert payload["pairlist"]["total"] == 8
    assert payload["pairlist"]["preview"][0] == "BTC/USDT:USDT"


def _log(level: LogLevel, code: str) -> LogEntryResponse:
    return LogEntryResponse(
        at=NOW,
        level=level,
        code=code,
        message=code.lower(),
        correlation_id=f"corr-{code}",
        command=None,
        route="/api/v1/dashboard/snapshot",
        safe_summary=code.lower(),
        report_hint="include support bundle",
    )
