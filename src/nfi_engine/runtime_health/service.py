from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from nfi_engine.config import RuntimeSettings
from nfi_engine.dashboard import DashboardReadModels
from nfi_engine.paper import BotState
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.runtime_health.checks import (
    database_check,
    heartbeat_check,
    manual_halt_check,
    next_action,
    overall_state,
    preflight_check,
    resource_check,
    wallet_check,
)
from nfi_engine.runtime_health.database import collect_database_snapshot
from nfi_engine.runtime_health.freshness import latest_dashboard_at
from nfi_engine.runtime_health.freshness_checks import (
    data_freshness_check,
    exchange_api_error_check,
    reconciliation_age_check,
    wallet_freshness_check,
)
from nfi_engine.runtime_health.live_pilot import (
    evaluate_restricted_live_pilot,
    live_pilot_health_check,
)
from nfi_engine.runtime_health.models import (
    RuntimeDatabaseSnapshot,
    RuntimeHealthCode,
    RuntimeHealthSnapshot,
    RuntimeResourceSnapshot,
)
from nfi_engine.runtime_health.resources import collect_runtime_resources
from nfi_engine.strategy.nfi_x7 import build_x7_semantic_status
from nfi_engine.wallet import WalletBalanceSnapshot


@dataclass(frozen=True, slots=True)
class RuntimeHealthRequest:
    settings: RuntimeSettings
    bot_state: BotState
    readiness: PreflightReport | None
    read_models: DashboardReadModels
    wallet_balance: WalletBalanceSnapshot
    now: datetime | None = None
    resources: RuntimeResourceSnapshot | None = None
    database: RuntimeDatabaseSnapshot | None = None
    exchange_api_errors: int = 0


def build_runtime_health_snapshot(request: RuntimeHealthRequest) -> RuntimeHealthSnapshot:
    generated_at = request.now if request.now is not None else datetime.now(UTC)
    resource_snapshot = (
        request.resources
        if request.resources is not None
        else collect_runtime_resources(path=_resource_path(request.settings), now=generated_at)
    )
    database_snapshot = (
        request.database
        if request.database is not None
        else collect_database_snapshot(
            database_url=request.settings.database.url,
            now=generated_at,
        )
    )
    checks = (
        heartbeat_check(request.bot_state),
        preflight_check(request.readiness),
        database_check(database_snapshot),
        wallet_check(request.wallet_balance),
        wallet_freshness_check(
            settings=request.settings,
            wallet=request.wallet_balance,
            generated_at=generated_at,
        ),
        data_freshness_check(
            settings=request.settings,
            read_models=request.read_models,
            generated_at=generated_at,
        ),
        reconciliation_age_check(
            settings=request.settings,
            read_models=request.read_models,
            generated_at=generated_at,
        ),
        exchange_api_error_check(
            settings=request.settings,
            error_count=request.exchange_api_errors,
        ),
        manual_halt_check(request.settings),
        live_pilot_health_check(
            evaluate_restricted_live_pilot(settings=request.settings, now=generated_at),
        ),
        resource_check(
            code=RuntimeHealthCode.DISK_BUDGET,
            state=resource_snapshot.disk_state,
            message=f"free_disk_bytes={resource_snapshot.free_disk_bytes}",
            blocked_action="Free disk space before starting a run.",
        ),
        resource_check(
            code=RuntimeHealthCode.MEMORY_BUDGET,
            state=resource_snapshot.memory_state,
            message=f"memory_rss_bytes={resource_snapshot.memory_rss_bytes}",
            blocked_action="Review memory use before running on Raspberry Pi 4.",
        ),
    )
    state = overall_state(checks)
    return RuntimeHealthSnapshot(
        generated_at=generated_at,
        state=state,
        next_action=next_action(checks, state),
        checks=checks,
        resources=resource_snapshot,
        database=database_snapshot,
        wallet_balance=request.wallet_balance,
        x7_semantic_status=build_x7_semantic_status(
            settings=request.settings,
            readiness=request.readiness,
            dashboard_data_observed=latest_dashboard_at(request.read_models) is not None,
        ),
    )


def _resource_path(settings: RuntimeSettings) -> Path:
    if settings.database.url.startswith("sqlite+aiosqlite:///"):
        database_path = settings.database.url.removeprefix("sqlite+aiosqlite:///")
        path = Path(database_path).parent
        if str(path) == "":
            return Path()
        return _existing_parent(path)
    return Path()


def _existing_parent(path: Path) -> Path:
    current = path
    while not current.exists() and current != current.parent:
        current = current.parent
    return current
