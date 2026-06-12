from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

from nfi_engine.api.models import LogEntryResponse
from nfi_engine.config import LogLevel, RuntimeSettings
from nfi_engine.dashboard.models import (
    DashboardError,
    DashboardPairlistSummary,
    DashboardReadiness,
    DashboardReadinessCheck,
    DashboardReadModels,
    DashboardSnapshot,
)
from nfi_engine.paper import BotState
from nfi_engine.preflight.models import PreflightReport

PAIR_PREVIEW_LIMIT: Final = 4
RECENT_ERROR_LIMIT: Final = 3


def build_dashboard_snapshot(
    *,
    settings: RuntimeSettings,
    bot_state: BotState,
    readiness: PreflightReport,
    logs: tuple[LogEntryResponse, ...],
    read_models: DashboardReadModels,
) -> DashboardSnapshot:
    return DashboardSnapshot(
        generated_at=datetime.now(UTC),
        bot_state=bot_state,
        trading_mode=settings.exchange.trading_mode.value,
        exchange=settings.exchange.name,
        readiness=_readiness(readiness),
        pairlist=_pairlist(settings),
        equity_points=read_models.equity_points,
        price_points=read_models.price_points,
        open_positions=read_models.open_positions,
        recent_trades=read_models.recent_trades,
        recent_errors=_recent_errors(logs),
    )


def _readiness(report: PreflightReport) -> DashboardReadiness:
    return DashboardReadiness(
        profile=report.profile,
        blocked=report.blocked,
        checks=tuple(
            DashboardReadinessCheck(
                code=check.code.value,
                status=check.status.value,
                message=check.message,
            )
            for check in report.checks
        ),
    )


def _pairlist(settings: RuntimeSettings) -> DashboardPairlistSummary:
    pairs = tuple(
        pair.strip() for pair in settings.pairlist.whitelist.split(",") if pair.strip() != ""
    )
    return DashboardPairlistSummary(
        total=len(pairs),
        preview=pairs[:PAIR_PREVIEW_LIMIT],
        quote_asset=settings.pairlist.quote_asset,
    )


def _recent_errors(logs: tuple[LogEntryResponse, ...]) -> tuple[DashboardError, ...]:
    return tuple(
        DashboardError(
            at=log.at,
            code=log.code,
            safe_summary=log.safe_summary,
            correlation_id=log.correlation_id,
        )
        for log in logs
        if log.level is LogLevel.ERROR
    )[:RECENT_ERROR_LIMIT]
