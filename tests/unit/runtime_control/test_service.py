from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from nfi_engine.config.models import EngineSettings, RuntimeSettings
from nfi_engine.paper import BotCommand, BotState
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.runtime_control import RuntimeControlCode, RuntimeControlRequest, control_runtime
from nfi_engine.runtime_health import (
    RuntimeDatabaseSnapshot,
    RuntimeHealthSnapshot,
    RuntimeHealthState,
    RuntimeResourceSnapshot,
)
from nfi_engine.strategy.nfi_x7 import build_x7_semantic_status
from nfi_engine.wallet import WalletBalanceCode, WalletBalanceSnapshot, WalletBalanceStatus


def test_pause_blocks_new_entries_when_runtime_is_running() -> None:
    # Given: a running runtime.
    request = _request(state=BotState.RUNNING, command=BotCommand.PAUSE)

    # When: the operator pauses entries.
    result = control_runtime(request)

    # Then: entries are blocked while the runtime remains inspectable.
    assert result.accepted is True
    assert result.state is BotState.PAUSED
    assert result.new_entries_allowed is False
    assert result.code is RuntimeControlCode.RUNTIME_CONTROL_ACCEPTED


def test_resume_requires_preflight_when_report_is_missing() -> None:
    # Given: a paused runtime with no preflight report.
    request = _request(
        state=BotState.PAUSED,
        command=BotCommand.RESUME,
        health=_health(RuntimeHealthState.HEALTHY),
    )

    # When: the operator resumes entries.
    result = control_runtime(request)

    # Then: resume is blocked with a stable preflight code.
    assert result.accepted is False
    assert result.state is BotState.PAUSED
    assert result.code is RuntimeControlCode.RUNTIME_PREFLIGHT_REQUIRED


def test_resume_when_runtime_health_is_blocked_keeps_entries_paused() -> None:
    # Given: a paused runtime with preflight pass but blocked runtime health.
    request = _request(
        state=BotState.PAUSED,
        command=BotCommand.RESUME,
        readiness=_ready(),
        health=_health(RuntimeHealthState.BLOCKED),
    )

    # When: the operator resumes entries.
    result = control_runtime(request)

    # Then: resume stays blocked and does not permit new entries.
    assert result.accepted is False
    assert result.state is BotState.PAUSED
    assert result.new_entries_allowed is False
    assert result.code is RuntimeControlCode.RUNTIME_HEALTH_BLOCKED


def test_start_when_live_trading_is_enabled_returns_live_unsafe() -> None:
    # Given: a stopped runtime with live trading intent enabled.
    request = _request(
        settings=RuntimeSettings(engine=EngineSettings(live_trading=True)),
        state=BotState.STOPPED,
        command=BotCommand.START,
        readiness=_ready(),
        health=_health(RuntimeHealthState.HEALTHY),
    )

    # When: the operator starts runtime entries.
    result = control_runtime(request)

    # Then: the control refuses to imply live execution readiness.
    assert result.accepted is False
    assert result.state is BotState.STOPPED
    assert result.code is RuntimeControlCode.RUNTIME_LIVE_UNSAFE


def test_stop_when_already_stopped_returns_stable_code() -> None:
    # Given: an already stopped runtime.
    request = _request(state=BotState.STOPPED, command=BotCommand.STOP)

    # When: the operator stops again.
    result = control_runtime(request)

    # Then: the response is a stable no-op denial.
    assert result.accepted is False
    assert result.state is BotState.STOPPED
    assert result.code is RuntimeControlCode.RUNTIME_ALREADY_STOPPED


def _request(
    *,
    state: BotState,
    command: BotCommand,
    settings: RuntimeSettings | None = None,
    readiness: PreflightReport | None = None,
    health: RuntimeHealthSnapshot | None = None,
) -> RuntimeControlRequest:
    return RuntimeControlRequest(
        settings=settings or RuntimeSettings(),
        state=state,
        command=command,
        readiness=readiness,
        health=health,
    )


def _ready() -> PreflightReport:
    return PreflightReport(profile="paper", blocked=False, checks=())


def _health(state: RuntimeHealthState) -> RuntimeHealthSnapshot:
    now = datetime(2026, 6, 15, tzinfo=UTC)
    return RuntimeHealthSnapshot(
        generated_at=now,
        state=state,
        next_action="runtime health fixture",
        checks=(),
        resources=RuntimeResourceSnapshot(
            captured_at=now,
            free_disk_bytes=1_000_000_000,
            memory_rss_bytes=100_000_000,
            disk_state=state,
            memory_state=RuntimeHealthState.HEALTHY,
        ),
        database=RuntimeDatabaseSnapshot(
            captured_at=now,
            readable=True,
            writable=True,
            state=state,
            message="database_path=test",
        ),
        wallet_balance=WalletBalanceSnapshot(
            status=WalletBalanceStatus.FETCHED,
            code=WalletBalanceCode.FETCHED,
            exchange="simulator",
            trading_mode="spot",
            captured_at=now,
            equity=Decimal(1000),
            available=Decimal(1000),
            quote_asset="USDT",
            position_count=0,
            next_action="wallet fixture",
            message="wallet fixture",
        ),
        x7_semantic_status=build_x7_semantic_status(settings=RuntimeSettings(), readiness=None),
    )
