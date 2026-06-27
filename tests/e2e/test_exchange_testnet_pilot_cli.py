from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


class _TestnetPilotTransitionPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    from_state: str
    to_state: str
    trigger: str
    idempotent: bool


class _TestnetPilotExecutionPlanPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    client_order_id: str
    dry_run_preview_required: bool
    kill_switch_required: bool
    reconciliation_required: bool
    idempotency_key_source: str
    transitions: tuple[_TestnetPilotTransitionPayload, ...]


class _TestnetPilotPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    exchange: str
    trading_mode: str
    testnet: bool
    pilot_ready: bool
    live_money_orders_enabled: bool
    sample_client_order_id: str
    execution_plan: _TestnetPilotExecutionPlanPayload
    blockers: tuple[str, ...]


def test_exchange_testnet_pilot_cli_reports_hardened_json(tmp_path: Path) -> None:
    # Given
    config = tmp_path / "binance-x7-testnet-pilot.yaml"
    config.write_text(
        """engine:
  live_trading: false
exchange:
  name: binance
  trading_mode: futures
  margin_mode: isolated
  testnet: true
  api_key: local-test-key
  api_secret: local-test-secret
  permission_read: enabled
  permission_trade: enabled
  permission_futures: enabled
  permission_withdrawal: disabled
  permission_ip_allowlist: enabled
strategy:
  name: X7NativeStrategy
  module: nfi_engine.strategy.nfi_x7:X7NativeStrategy
reconciliation:
  required: true
  fixture_path: tests/fixtures/exchange/reconcile_match.json
circuit_breakers:
  enabled: true
  max_daily_loss_usdt: "50"
  max_drawdown_pct: "0.20"
  max_stale_seconds: 300
  max_api_errors: 5
  max_rejected_orders: 10
  manual_halt_file: .runtime/manual-halt.flag
""",
        encoding="utf-8",
    )
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "testnet-pilot",
        "--config",
        str(config),
        "--json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    validation = subprocess.run(
        [sys.executable, "-m", "json.tool"],
        cwd=PROJECT_ROOT,
        input=result.stdout,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = _TestnetPilotPayload.model_validate_json(result.stdout)

    # Then
    assert result.returncode == 0, result.stderr
    assert validation.returncode == 0, validation.stderr
    assert payload.exchange == "binance"
    assert payload.trading_mode == "futures"
    assert payload.testnet is True
    assert payload.pilot_ready is True
    assert payload.live_money_orders_enabled is False
    assert payload.blockers == ()
    assert payload.sample_client_order_id.startswith("nfi-tn-")
    assert payload.execution_plan.client_order_id == payload.sample_client_order_id
    assert payload.execution_plan.dry_run_preview_required is True
    assert payload.execution_plan.kill_switch_required is True
    assert payload.execution_plan.reconciliation_required is True
    assert "strategy" in payload.execution_plan.idempotency_key_source
    assert _transition_triggers(payload.execution_plan) >= {
        "partial_fill",
        "kill_switch_or_cancel",
        "startup_or_post_order_reconcile",
    }
    assert "local-test-secret" not in result.stdout
    assert "local-test-secret" not in result.stderr


def test_exchange_testnet_pilot_cli_keeps_example_config_blocked() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "testnet-pilot",
        "--config",
        "examples/futures-paper.yaml",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "pilot_ready=false" in result.stdout
    assert "live_money_orders_enabled=false" in result.stdout
    assert "dry_run_preview_required=true" in result.stdout
    assert "kill_switch_required=true" in result.stdout
    assert "transition=acknowledged->partially_filled" in result.stdout
    assert "TESTNET_PILOT_CREDENTIALS_MISSING" in result.stdout


def _transition_triggers(plan: _TestnetPilotExecutionPlanPayload) -> set[str]:
    return {transition.trigger for transition in plan.transitions}
