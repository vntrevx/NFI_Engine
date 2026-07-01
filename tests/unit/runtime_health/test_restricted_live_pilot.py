from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

from nfi_engine.config.models import (
    CircuitBreakerSettings,
    RestrictedLivePilotSettings,
    RiskSettings,
    RuntimeSettings,
)
from nfi_engine.dashboard import DashboardReadModels
from nfi_engine.paper import BotCommand, BotState
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.runtime_control import RuntimeControlRequest, control_runtime
from nfi_engine.runtime_control.models import RuntimeControlCode
from nfi_engine.runtime_health import (
    RuntimeDatabaseSnapshot,
    RuntimeHealthCode,
    RuntimeHealthRequest,
    RuntimeHealthSnapshot,
    RuntimeHealthState,
    RuntimeResourceSnapshot,
    build_runtime_health_snapshot,
)
from nfi_engine.runtime_health.live_pilot import evaluate_restricted_live_pilot
from nfi_engine.runtime_health.live_pilot_models import RestrictedLivePilotCode
from nfi_engine.wallet import WalletBalanceCode, WalletBalanceSnapshot, WalletBalanceStatus

NOW = datetime(2026, 6, 30, 12, 0, tzinfo=UTC)


def test_restricted_live_pilot_blocks_without_canary_pass_marker(tmp_path: Path) -> None:
    # Given: pilot config points at a marker that does not exist.
    settings = _settings(tmp_path, marker_exists=False)

    # When
    status = evaluate_restricted_live_pilot(settings=settings, now=NOW)

    # Then
    assert status.state is RuntimeHealthState.BLOCKED
    assert status.code is RestrictedLivePilotCode.CANARY_MARKER
    assert "missing" in status.message


def test_restricted_live_pilot_blocks_unsanitized_canary_pass_marker(tmp_path: Path) -> None:
    # Given: a legacy status-only marker without sanitized execution proof fields.
    settings = _settings(tmp_path, marker_exists=True)
    marker = Path(settings.restricted_live_pilot.canary_pass_marker_path or "")
    marker.write_text('{"live_canary_status":"pass"}\n', encoding="utf-8")

    # When
    status = evaluate_restricted_live_pilot(settings=settings, now=NOW)

    # Then
    assert status.state is RuntimeHealthState.BLOCKED
    assert status.code is RestrictedLivePilotCode.CANARY_MARKER
    assert "sanitized" in status.message


def test_restricted_live_pilot_allows_dry_run_harness_with_pass_marker(tmp_path: Path) -> None:
    # Given: a sanitized canary-pass marker and explicit pilot bounds.
    settings = _settings(tmp_path, marker_exists=True)

    # When
    status = evaluate_restricted_live_pilot(settings=settings, now=NOW)

    # Then
    assert status.state is RuntimeHealthState.HEALTHY
    assert status.code is RestrictedLivePilotCode.READY
    assert status.pair_allowlist == ("BTC/USDT:USDT",)


def test_restricted_live_pilot_blocks_stale_reconciliation(tmp_path: Path) -> None:
    # Given: live pilot proof timestamps outside the configured interval.
    settings = _settings(
        tmp_path,
        marker_exists=True,
        reconciliation_captured_at=NOW - timedelta(seconds=400),
    )

    # When
    status = evaluate_restricted_live_pilot(settings=settings, now=NOW)

    # Then
    assert status.state is RuntimeHealthState.BLOCKED
    assert status.code is RestrictedLivePilotCode.FRESHNESS
    assert "reconciliation_age_seconds" in status.message


def test_restricted_live_pilot_blocks_stale_canary_pass_marker(tmp_path: Path) -> None:
    # Given: the canary-pass marker itself is older than the configured proof interval.
    settings = _settings(
        tmp_path,
        marker_exists=True,
        marker_generated_at=NOW - timedelta(seconds=400),
    )

    # When
    status = evaluate_restricted_live_pilot(settings=settings, now=NOW)

    # Then
    assert status.state is RuntimeHealthState.BLOCKED
    assert status.code is RestrictedLivePilotCode.CANARY_MARKER
    assert "canary_marker_age_seconds" in status.message


def test_runtime_health_reports_live_pilot_and_blocks_new_entries(tmp_path: Path) -> None:
    # Given: runtime health includes an active pilot blocker.
    settings = _settings(tmp_path, marker_exists=False)
    snapshot = build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=settings,
            bot_state=BotState.STOPPED,
            readiness=PreflightReport(profile="restricted-live", blocked=False, checks=()),
            read_models=DashboardReadModels.empty(),
            wallet_balance=_wallet(),
            now=NOW,
            resources=_resources(),
            database=_database(),
        ),
    )

    # When: runtime control tries to start entries.
    result = control_runtime(
        RuntimeControlRequest(
            settings=settings,
            state=BotState.STOPPED,
            command=BotCommand.START,
            readiness=PreflightReport(profile="restricted-live", blocked=False, checks=()),
            health=snapshot,
        ),
    )

    # Then: the live-pilot health code is visible and start is denied.
    assert snapshot.state is RuntimeHealthState.BLOCKED
    assert _check_state(snapshot, RuntimeHealthCode.LIVE_PILOT) is RuntimeHealthState.BLOCKED
    assert result.accepted is False
    assert result.code is RuntimeControlCode.RUNTIME_HEALTH_BLOCKED
    assert result.new_entries_allowed is False


def _settings(
    tmp_path: Path,
    *,
    marker_exists: bool,
    reconciliation_captured_at: datetime = NOW,
    marker_generated_at: datetime = NOW,
) -> RuntimeSettings:
    marker = tmp_path / "live-canary-pass.json"
    halt_file = tmp_path / "manual-halt.flag"
    if marker_exists:
        marker.write_text(
            f"{json.dumps(_marker_payload(marker_generated_at), sort_keys=True)}\n",
            encoding="utf-8",
        )
    return RuntimeSettings(
        risk=RiskSettings(max_open_trades=1, max_leverage=Decimal(2)),
        circuit_breakers=CircuitBreakerSettings(enabled=True),
        restricted_live_pilot=RestrictedLivePilotSettings(
            enabled=True,
            canary_pass_marker_path=str(marker),
            pair_allowlist="BTC/USDT:USDT",
            stake_usdt=Decimal(5),
            leverage=Decimal(1),
            max_open_trades=1,
            max_daily_loss_usdt=Decimal(2),
            manual_halt_file=str(halt_file),
            reconciliation_interval_seconds=300,
            wallet_sync_interval_seconds=300,
            runtime_duration_seconds=86400,
            reconciliation_captured_at=reconciliation_captured_at,
            wallet_balance_captured_at=NOW,
        ),
    )


def _marker_payload(generated_at: datetime) -> dict[str, object]:
    return {
        "canary_notional_usdt": "5",
        "config_hash": "local-config-hash",
        "entry_order_id": "entry-1",
        "exit_order_id": "exit-1",
        "final_reconciliation_status": "reconciled",
        "generated_at": generated_at.isoformat(),
        "live_canary_status": "pass",
        "owner_approval_ref": "owner-approved-local-test",
        "pair": "BTC/USDT:USDT",
        "preview_hash": "preview-hash",
        "reduce_only_exit": True,
        "rollback_receipt": True,
        "wallet_before_after": True,
    }


def _wallet() -> WalletBalanceSnapshot:
    return WalletBalanceSnapshot(
        status=WalletBalanceStatus.FETCHED,
        code=WalletBalanceCode.FETCHED,
        exchange="binance",
        trading_mode="futures",
        captured_at=NOW,
        equity=Decimal(1000),
        available=Decimal(990),
        quote_asset="USDT",
        position_count=0,
        next_action="No wallet action required.",
        message="wallet fetched",
    )


def _resources() -> RuntimeResourceSnapshot:
    return RuntimeResourceSnapshot(
        captured_at=NOW,
        free_disk_bytes=1024 * 1024 * 1024,
        memory_rss_bytes=128 * 1024 * 1024,
        disk_state=RuntimeHealthState.HEALTHY,
        memory_state=RuntimeHealthState.HEALTHY,
    )


def _database() -> RuntimeDatabaseSnapshot:
    return RuntimeDatabaseSnapshot(
        captured_at=NOW,
        readable=True,
        writable=True,
        state=RuntimeHealthState.HEALTHY,
        message="database readable and writable",
    )


def _check_state(snapshot: RuntimeHealthSnapshot, code: RuntimeHealthCode) -> RuntimeHealthState:
    for check in snapshot.checks:
        if check.code is code:
            return check.state
    msg = f"missing check {code.value}"
    raise AssertionError(msg)
