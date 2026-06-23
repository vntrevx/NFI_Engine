from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.dashboard import DashboardReadModels
from nfi_engine.paper import BotState
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.runtime_health.freshness import latest_dashboard_at
from nfi_engine.runtime_health.models import (
    RuntimeHealthCheck,
    RuntimeHealthCode,
    RuntimeHealthSnapshot,
    RuntimeHealthState,
    RuntimeResourceSnapshot,
)
from nfi_engine.runtime_health.resources import collect_runtime_resources
from nfi_engine.strategy.nfi_x7 import build_x7_semantic_status
from nfi_engine.wallet import WalletBalanceSnapshot, WalletBalanceStatus

CLOCK_SKEW_GRACE_SECONDS = 60


@dataclass(frozen=True, slots=True)
class RuntimeHealthRequest:
    settings: RuntimeSettings
    bot_state: BotState
    readiness: PreflightReport | None
    read_models: DashboardReadModels
    wallet_balance: WalletBalanceSnapshot
    now: datetime | None = None
    resources: RuntimeResourceSnapshot | None = None


def build_runtime_health_snapshot(request: RuntimeHealthRequest) -> RuntimeHealthSnapshot:
    generated_at = request.now if request.now is not None else datetime.now(UTC)
    resource_snapshot = (
        request.resources
        if request.resources is not None
        else collect_runtime_resources(path=_resource_path(request.settings), now=generated_at)
    )
    checks = (
        _heartbeat_check(request.bot_state),
        _preflight_check(request.readiness),
        _wallet_check(request.wallet_balance),
        _freshness_check(
            settings=request.settings,
            read_models=request.read_models,
            generated_at=generated_at,
        ),
        _manual_halt_check(request.settings),
        _resource_check(
            code=RuntimeHealthCode.DISK_BUDGET,
            state=resource_snapshot.disk_state,
            message=f"free_disk_bytes={resource_snapshot.free_disk_bytes}",
            blocked_action="Free disk space before starting a run.",
        ),
        _resource_check(
            code=RuntimeHealthCode.MEMORY_BUDGET,
            state=resource_snapshot.memory_state,
            message=f"memory_rss_bytes={resource_snapshot.memory_rss_bytes}",
            blocked_action="Review memory use before running on Raspberry Pi 4.",
        ),
    )
    state = _overall_state(checks)
    return RuntimeHealthSnapshot(
        generated_at=generated_at,
        state=state,
        next_action=_next_action(checks, state),
        checks=checks,
        resources=resource_snapshot,
        wallet_balance=request.wallet_balance,
        x7_semantic_status=build_x7_semantic_status(
            settings=request.settings,
            readiness=request.readiness,
            dashboard_data_observed=latest_dashboard_at(request.read_models) is not None,
        ),
    )


def _heartbeat_check(bot_state: BotState) -> RuntimeHealthCheck:
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.ENGINE_HEARTBEAT,
        state=RuntimeHealthState.HEALTHY,
        message=f"bot_state={bot_state.value}",
        next_action="No heartbeat action required.",
    )


def _preflight_check(readiness: PreflightReport | None) -> RuntimeHealthCheck:
    if readiness is None:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.PREFLIGHT,
            state=RuntimeHealthState.DEGRADED,
            message="preflight report is not loaded",
            next_action="Run preflight before starting a run.",
        )
    if readiness.blocked:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.PREFLIGHT,
            state=RuntimeHealthState.BLOCKED,
            message="preflight is blocking startup",
            next_action="Open Settings and fix blocked preflight checks.",
        )
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.PREFLIGHT,
        state=RuntimeHealthState.HEALTHY,
        message="preflight checks are not blocking startup",
        next_action="No preflight action required.",
    )


def _wallet_check(wallet: WalletBalanceSnapshot) -> RuntimeHealthCheck:
    match wallet.status:
        case WalletBalanceStatus.FETCHED:
            state = RuntimeHealthState.HEALTHY
        case WalletBalanceStatus.BLOCKED:
            state = RuntimeHealthState.BLOCKED
        case WalletBalanceStatus.UNAVAILABLE | WalletBalanceStatus.ERROR:
            state = RuntimeHealthState.DEGRADED
        case unreachable:
            assert_never(unreachable)
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.WALLET_BALANCE,
        state=state,
        message=wallet.code.value,
        next_action=wallet.next_action,
    )


def _freshness_check(
    *,
    settings: RuntimeSettings,
    read_models: DashboardReadModels,
    generated_at: datetime,
) -> RuntimeHealthCheck:
    latest_at = latest_dashboard_at(read_models)
    if latest_at is None:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.DATA_FRESHNESS,
            state=RuntimeHealthState.DEGRADED,
            message="no dashboard data has been recorded yet",
            next_action="Run paper/testnet once to seed dashboard health data.",
        )
    if latest_at > generated_at + timedelta(seconds=CLOCK_SKEW_GRACE_SECONDS):
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.CLOCK_SKEW,
            state=RuntimeHealthState.BLOCKED,
            message=f"latest_runtime_at={latest_at.isoformat()}",
            next_action="Fix system clock skew before starting a run.",
        )
    stale_after = timedelta(seconds=settings.circuit_breakers.max_stale_seconds)
    if generated_at - latest_at > stale_after:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.DATA_FRESHNESS,
            state=RuntimeHealthState.BLOCKED,
            message=f"latest_runtime_at={latest_at.isoformat()}",
            next_action="Refresh market data before starting a run.",
        )
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.DATA_FRESHNESS,
        state=RuntimeHealthState.HEALTHY,
        message=f"latest_runtime_at={latest_at.isoformat()}",
        next_action="No data freshness action required.",
    )


def _manual_halt_check(settings: RuntimeSettings) -> RuntimeHealthCheck:
    if _manual_halt_active(settings):
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.CIRCUIT_BREAKER_STATE,
            state=RuntimeHealthState.BLOCKED,
            message="manual halt is enabled",
            next_action="Disable manual halt only after reviewing the reason.",
        )
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.CIRCUIT_BREAKER_STATE,
        state=RuntimeHealthState.HEALTHY,
        message="manual halt is disabled",
        next_action="No circuit-breaker action required.",
    )


def _manual_halt_active(settings: RuntimeSettings) -> bool:
    circuit_breakers = settings.circuit_breakers
    return circuit_breakers.manual_halt or _manual_halt_file_exists(
        circuit_breakers.manual_halt_file
    )


def _manual_halt_file_exists(raw_path: str | None) -> bool:
    if raw_path is None:
        return False
    path = raw_path.strip()
    if path == "":
        return False
    return Path(path).exists()


def _resource_check(
    *,
    code: RuntimeHealthCode,
    state: RuntimeHealthState,
    message: str,
    blocked_action: str,
) -> RuntimeHealthCheck:
    if state is RuntimeHealthState.HEALTHY:
        return RuntimeHealthCheck(
            code=code,
            state=state,
            message=message,
            next_action="No resource action required.",
        )
    return RuntimeHealthCheck(
        code=code,
        state=state,
        message=message,
        next_action=blocked_action,
    )


def _overall_state(checks: tuple[RuntimeHealthCheck, ...]) -> RuntimeHealthState:
    if any(check.state is RuntimeHealthState.BLOCKED for check in checks):
        return RuntimeHealthState.BLOCKED
    if any(check.state is RuntimeHealthState.DEGRADED for check in checks):
        return RuntimeHealthState.DEGRADED
    return RuntimeHealthState.HEALTHY


def _next_action(
    checks: tuple[RuntimeHealthCheck, ...],
    state: RuntimeHealthState,
) -> str:
    for check in checks:
        if check.state is state and state is not RuntimeHealthState.HEALTHY:
            return check.next_action
    return "Runtime health is ready for paper/testnet operation."


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
