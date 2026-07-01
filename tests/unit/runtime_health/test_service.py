from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from nfi_engine.config.models import CircuitBreakerSettings, RuntimeSettings
from nfi_engine.dashboard import (
    DashboardEquityPoint,
    DashboardExecutionEvent,
    DashboardReadModels,
)
from nfi_engine.execution import ExecutionEventType, ExecutionState
from nfi_engine.paper import BotState
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.runtime_health import (
    RuntimeDatabaseSnapshot,
    RuntimeHealthCode,
    RuntimeHealthRequest,
    RuntimeHealthSnapshot,
    RuntimeHealthState,
    RuntimeResourceSnapshot,
    build_runtime_health_snapshot,
)
from nfi_engine.wallet import WalletBalanceCode, WalletBalanceSnapshot, WalletBalanceStatus

NOW = datetime(2026, 6, 15, tzinfo=UTC)


def test_runtime_health_is_healthy_for_fresh_data_and_fetched_wallet() -> None:
    # Given: fresh dashboard data, passing preflight, and a fetched wallet balance.
    snapshot = build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=RuntimeSettings(),
            bot_state=BotState.RUNNING,
            readiness=PreflightReport(profile="paper", blocked=False, checks=()),
            read_models=_read_models(NOW),
            wallet_balance=_wallet(WalletBalanceStatus.FETCHED),
            now=NOW,
            resources=_resources(RuntimeHealthState.HEALTHY, RuntimeHealthState.HEALTHY),
            database=_database(RuntimeHealthState.HEALTHY),
        ),
    )

    # Then: the aggregate health is ready for paper/testnet operation.
    assert snapshot.state is RuntimeHealthState.HEALTHY
    assert snapshot.next_action == "Runtime health is ready for paper/testnet operation."
    assert _check_state(snapshot, RuntimeHealthCode.WALLET_BALANCE) is RuntimeHealthState.HEALTHY


def test_runtime_health_blocks_stale_runtime_data() -> None:
    # Given: dashboard data older than the configured stale-data guard.
    snapshot = build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=RuntimeSettings(),
            bot_state=BotState.RUNNING,
            readiness=PreflightReport(profile="paper", blocked=False, checks=()),
            read_models=_read_models(NOW - timedelta(seconds=400)),
            wallet_balance=_wallet(WalletBalanceStatus.FETCHED),
            now=NOW,
            resources=_resources(RuntimeHealthState.HEALTHY, RuntimeHealthState.HEALTHY),
            database=_database(RuntimeHealthState.HEALTHY),
        ),
    )

    # Then: stale market/runtime state blocks startup.
    assert snapshot.state is RuntimeHealthState.BLOCKED
    assert _check_state(snapshot, RuntimeHealthCode.DATA_FRESHNESS) is RuntimeHealthState.BLOCKED


def test_runtime_health_blocks_future_clock_skew() -> None:
    # Given: persisted dashboard data from the future.
    snapshot = build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=RuntimeSettings(),
            bot_state=BotState.RUNNING,
            readiness=PreflightReport(profile="paper", blocked=False, checks=()),
            read_models=_read_models(NOW + timedelta(seconds=120)),
            wallet_balance=_wallet(WalletBalanceStatus.FETCHED),
            now=NOW,
            resources=_resources(RuntimeHealthState.HEALTHY, RuntimeHealthState.HEALTHY),
            database=_database(RuntimeHealthState.HEALTHY),
        ),
    )

    # Then: clock skew has a dedicated blocker code.
    assert snapshot.state is RuntimeHealthState.BLOCKED
    assert _check_state(snapshot, RuntimeHealthCode.CLOCK_SKEW) is RuntimeHealthState.BLOCKED


def test_runtime_health_degrades_when_wallet_adapter_is_unavailable() -> None:
    # Given: no live dashboard data yet and no wallet adapter.
    snapshot = build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=RuntimeSettings(),
            bot_state=BotState.STOPPED,
            readiness=PreflightReport(profile="paper", blocked=False, checks=()),
            read_models=DashboardReadModels.empty(),
            wallet_balance=_wallet(WalletBalanceStatus.UNAVAILABLE),
            now=NOW,
            resources=_resources(RuntimeHealthState.HEALTHY, RuntimeHealthState.HEALTHY),
            database=_database(RuntimeHealthState.HEALTHY),
        ),
    )

    # Then: the operator gets degraded health rather than a false live-ready signal.
    assert snapshot.state is RuntimeHealthState.DEGRADED
    assert _check_state(snapshot, RuntimeHealthCode.WALLET_BALANCE) is RuntimeHealthState.DEGRADED


def test_runtime_health_blocks_manual_halt_file(tmp_path: Path) -> None:
    # Given: the operator has dropped a manual halt file on disk.
    halt_file = tmp_path / "manual-halt"
    halt_file.write_text("halt\n", encoding="utf-8")

    snapshot = build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=RuntimeSettings(
                circuit_breakers=CircuitBreakerSettings(manual_halt_file=str(halt_file)),
            ),
            bot_state=BotState.RUNNING,
            readiness=PreflightReport(profile="paper", blocked=False, checks=()),
            read_models=_read_models(NOW),
            wallet_balance=_wallet(WalletBalanceStatus.FETCHED),
            now=NOW,
            resources=_resources(RuntimeHealthState.HEALTHY, RuntimeHealthState.HEALTHY),
            database=_database(RuntimeHealthState.HEALTHY),
        ),
    )

    # Then: file-based manual halt blocks runtime promotion like an active breaker.
    assert snapshot.state is RuntimeHealthState.BLOCKED
    assert (
        _check_state(snapshot, RuntimeHealthCode.CIRCUIT_BREAKER_STATE)
        is RuntimeHealthState.BLOCKED
    )


def test_runtime_health_blocks_stale_wallet_snapshot() -> None:
    snapshot = build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=RuntimeSettings(),
            bot_state=BotState.RUNNING,
            readiness=PreflightReport(profile="paper", blocked=False, checks=()),
            read_models=_read_models(NOW),
            wallet_balance=_wallet(
                WalletBalanceStatus.FETCHED,
                captured_at=NOW - timedelta(seconds=400),
            ),
            now=NOW,
            resources=_resources(RuntimeHealthState.HEALTHY, RuntimeHealthState.HEALTHY),
            database=_database(RuntimeHealthState.HEALTHY),
        ),
    )

    assert snapshot.state is RuntimeHealthState.BLOCKED
    assert _check_state(snapshot, RuntimeHealthCode.WALLET_FRESHNESS) is RuntimeHealthState.BLOCKED


def test_runtime_health_blocks_database_without_write_access() -> None:
    snapshot = build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=RuntimeSettings(),
            bot_state=BotState.RUNNING,
            readiness=PreflightReport(profile="paper", blocked=False, checks=()),
            read_models=_read_models(NOW),
            wallet_balance=_wallet(WalletBalanceStatus.FETCHED),
            now=NOW,
            resources=_resources(RuntimeHealthState.HEALTHY, RuntimeHealthState.HEALTHY),
            database=_database(RuntimeHealthState.BLOCKED, writable=False),
        ),
    )

    assert snapshot.state is RuntimeHealthState.BLOCKED
    assert _check_state(snapshot, RuntimeHealthCode.DATABASE) is RuntimeHealthState.BLOCKED


def test_runtime_health_blocks_high_exchange_api_error_count() -> None:
    snapshot = build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=RuntimeSettings(),
            bot_state=BotState.RUNNING,
            readiness=PreflightReport(profile="paper", blocked=False, checks=()),
            read_models=_read_models(NOW),
            wallet_balance=_wallet(WalletBalanceStatus.FETCHED),
            now=NOW,
            resources=_resources(RuntimeHealthState.HEALTHY, RuntimeHealthState.HEALTHY),
            database=_database(RuntimeHealthState.HEALTHY),
            exchange_api_errors=5,
        ),
    )

    assert snapshot.state is RuntimeHealthState.BLOCKED
    assert (
        _check_state(snapshot, RuntimeHealthCode.EXCHANGE_API_ERRORS) is RuntimeHealthState.BLOCKED
    )


def _read_models(at: datetime) -> DashboardReadModels:
    return DashboardReadModels(
        equity_points=(DashboardEquityPoint(at=at, equity=Decimal(1000), available=Decimal(900)),),
        recent_execution_events=(
            DashboardExecutionEvent(
                event_id=1,
                intent_id="intent-1",
                event_type=ExecutionEventType.RECONCILED,
                state=ExecutionState.RECONCILED,
                message="reconciliation clear",
                raw_status_code="RECONCILIATION_CLEAR",
                metadata_json='{"issue_codes":[],"mismatch_count":0,"trading_halted":false}',
                occurred_at=at,
            ),
        ),
    )


def _wallet(
    status: WalletBalanceStatus,
    *,
    captured_at: datetime | None = None,
) -> WalletBalanceSnapshot:
    return WalletBalanceSnapshot(
        status=status,
        code=_wallet_code(status),
        exchange="simulator",
        trading_mode="spot",
        captured_at=(
            captured_at
            if captured_at is not None
            else NOW
            if status is WalletBalanceStatus.FETCHED
            else None
        ),
        equity=Decimal(1000) if status is WalletBalanceStatus.FETCHED else None,
        available=Decimal(900) if status is WalletBalanceStatus.FETCHED else None,
        quote_asset="USDT",
        position_count=0,
        next_action="wallet action",
        message="wallet message",
    )


def _wallet_code(status: WalletBalanceStatus) -> WalletBalanceCode:
    if status is WalletBalanceStatus.FETCHED:
        return WalletBalanceCode.FETCHED
    return WalletBalanceCode.ADAPTER_UNAVAILABLE


def _resources(
    disk_state: RuntimeHealthState,
    memory_state: RuntimeHealthState,
) -> RuntimeResourceSnapshot:
    return RuntimeResourceSnapshot(
        captured_at=NOW,
        free_disk_bytes=1024 * 1024 * 1024,
        memory_rss_bytes=128 * 1024 * 1024,
        disk_state=disk_state,
        memory_state=memory_state,
    )


def _database(
    state: RuntimeHealthState,
    *,
    readable: bool = True,
    writable: bool = True,
) -> RuntimeDatabaseSnapshot:
    return RuntimeDatabaseSnapshot(
        captured_at=NOW,
        readable=readable,
        writable=writable,
        state=state,
        message="database_path=test",
    )


def _check_state(snapshot: RuntimeHealthSnapshot, code: RuntimeHealthCode) -> RuntimeHealthState:
    for check in snapshot.checks:
        if check.code is code:
            return check.state
    raise AssertionError(code.value)
