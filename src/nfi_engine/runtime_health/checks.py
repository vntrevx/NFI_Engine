from __future__ import annotations

from pathlib import Path
from typing import assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.paper import BotState
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.runtime_health.models import (
    RuntimeDatabaseSnapshot,
    RuntimeHealthCheck,
    RuntimeHealthCode,
    RuntimeHealthState,
)
from nfi_engine.wallet import WalletBalanceSnapshot, WalletBalanceStatus


def heartbeat_check(bot_state: BotState) -> RuntimeHealthCheck:
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.ENGINE_HEARTBEAT,
        state=RuntimeHealthState.HEALTHY,
        message=f"bot_state={bot_state.value}",
        next_action="No heartbeat action required.",
    )


def preflight_check(readiness: PreflightReport | None) -> RuntimeHealthCheck:
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


def wallet_check(wallet: WalletBalanceSnapshot) -> RuntimeHealthCheck:
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


def database_check(database: RuntimeDatabaseSnapshot) -> RuntimeHealthCheck:
    if database.state is RuntimeHealthState.HEALTHY:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.DATABASE,
            state=database.state,
            message=database.message,
            next_action="No database action required.",
        )
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.DATABASE,
        state=database.state,
        message=database.message,
        next_action="Restore database read/write access before starting a run.",
    )


def manual_halt_check(settings: RuntimeSettings) -> RuntimeHealthCheck:
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


def resource_check(
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


def overall_state(checks: tuple[RuntimeHealthCheck, ...]) -> RuntimeHealthState:
    if any(check.state is RuntimeHealthState.BLOCKED for check in checks):
        return RuntimeHealthState.BLOCKED
    if any(check.state is RuntimeHealthState.DEGRADED for check in checks):
        return RuntimeHealthState.DEGRADED
    return RuntimeHealthState.HEALTHY


def next_action(
    checks: tuple[RuntimeHealthCheck, ...],
    state: RuntimeHealthState,
) -> str:
    for check in checks:
        if check.state is state and state is not RuntimeHealthState.HEALTHY:
            return check.next_action
    return "Runtime health is ready for paper/testnet operation."


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
