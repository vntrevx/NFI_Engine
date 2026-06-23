from __future__ import annotations

from datetime import UTC, datetime
from typing import Final

from nfi_engine.api.models import LogEntryResponse
from nfi_engine.config import LogLevel, RuntimeSettings
from nfi_engine.dashboard.models import (
    DashboardAction,
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
ACTION_LIMIT: Final = 4

READINESS_BLOCKED_ACTION: Final = DashboardAction(
    code="readiness_blocked",
    severity="error",
    title="Preflight is blocking startup",
    detail="Review failed checks in setup before starting the runtime.",
    target="settings/setup",
)
RUNTIME_ERRORS_ACTION: Final = DashboardAction(
    code="runtime_errors_detected",
    severity="error",
    title="Recent runtime errors need review",
    detail="Open Logs and inspect the latest error summaries before continuing.",
    target="logs",
)
PAIRLIST_EMPTY_ACTION: Final = DashboardAction(
    code="pairlist_empty",
    severity="warning",
    title="Pairlist is empty",
    detail="Add at least one whitelisted pair before running the paper engine.",
    target="settings",
)
PAPER_READY_ACTION: Final = DashboardAction(
    code="paper_runtime_ready",
    severity="info",
    title="Paper/testnet runtime is ready",
    detail="Review status, pairlist, and safety panels before starting the bot.",
    target="dashboard/status",
)
PREFLIGHT_MISSING_ACTION: Final = DashboardAction(
    code="preflight_not_loaded",
    severity="warning",
    title="Run preflight before starting",
    detail="Load a preflight report to confirm setup, storage, and safety gates.",
    target="settings/setup",
)
SUPPORT_BUNDLE_ACTION: Final = DashboardAction(
    code="support_bundle_follow_up",
    severity="info",
    title="Export a support bundle if errors persist",
    detail="Capture a redacted support bundle after reviewing the logs if follow-up is needed.",
    target="logs/support-bundle",
)


def build_dashboard_snapshot(
    *,
    settings: RuntimeSettings,
    bot_state: BotState,
    readiness: PreflightReport,
    logs: tuple[LogEntryResponse, ...],
    read_models: DashboardReadModels,
) -> DashboardSnapshot:
    pairlist = _pairlist(settings)
    recent_errors = _recent_errors(logs)
    return DashboardSnapshot(
        generated_at=datetime.now(UTC),
        bot_state=bot_state,
        trading_mode=settings.exchange.trading_mode.value,
        exchange=settings.exchange.name,
        actions=_dashboard_actions(
            readiness=readiness,
            pairlist=pairlist,
            recent_errors=recent_errors,
        ),
        readiness=_readiness(readiness),
        pairlist=pairlist,
        equity_points=read_models.equity_points,
        price_points=read_models.price_points,
        open_positions=read_models.open_positions,
        recent_trades=read_models.recent_trades,
        recent_errors=recent_errors,
    )


def build_dashboard_actions(
    *,
    settings: RuntimeSettings,
    readiness: PreflightReport | None,
    logs: tuple[LogEntryResponse, ...],
) -> tuple[DashboardAction, ...]:
    pairlist = _pairlist(settings)
    recent_errors = _recent_errors(logs)
    return _dashboard_actions(
        readiness=readiness,
        pairlist=pairlist,
        recent_errors=recent_errors,
    )


def _dashboard_actions(
    *,
    readiness: PreflightReport | None,
    pairlist: DashboardPairlistSummary,
    recent_errors: tuple[DashboardError, ...],
) -> tuple[DashboardAction, ...]:
    actions: list[DashboardAction] = []

    if readiness is None:
        actions.append(PREFLIGHT_MISSING_ACTION)
    elif readiness.blocked:
        actions.append(READINESS_BLOCKED_ACTION)

    if len(recent_errors) > 0:
        actions.append(RUNTIME_ERRORS_ACTION)

    if pairlist.total == 0:
        actions.append(PAIRLIST_EMPTY_ACTION)

    if len(actions) == 0:
        actions.append(PAPER_READY_ACTION)

    if len(recent_errors) > 0:
        actions.append(SUPPORT_BUNDLE_ACTION)

    return tuple(actions[:ACTION_LIMIT])


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
