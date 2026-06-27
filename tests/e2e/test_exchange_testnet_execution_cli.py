from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
_HARDENED_TESTNET_CONFIG_LINES: Final = (
    "engine:",
    "  live_trading: false",
    "exchange:",
    "  name: binance",
    "  trading_mode: futures",
    "  margin_mode: isolated",
    "  testnet: true",
    "  api_key: local-test-key",
    "  api_secret: local-test-secret",
    "  permission_read: enabled",
    "  permission_trade: enabled",
    "  permission_futures: enabled",
    "  permission_withdrawal: disabled",
    "  permission_ip_allowlist: enabled",
    "strategy:",
    "  name: X7NativeStrategy",
    "  module: nfi_engine.strategy.nfi_x7:X7NativeStrategy",
    "reconciliation:",
    "  required: true",
    "  fixture_path: tests/fixtures/exchange/reconcile_match.json",
    "circuit_breakers:",
    "  enabled: true",
    '  max_daily_loss_usdt: "50"',
    '  max_drawdown_pct: "0.20"',
    "  max_stale_seconds: 300",
    "  max_api_errors: 5",
    "  max_rejected_orders: 10",
    "  manual_halt_file: .runtime/manual-halt.flag",
)


class _TestnetExecutionEventPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    state: str
    source: str


class _TestnetExecutionPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    exchange: str
    trading_mode: str
    testnet: bool
    execution_ready: bool
    live_money_orders_enabled: bool
    live_exchange_observed: bool
    client_order_id: str
    submitted_order_id: str | None
    adapter_order_state: str | None
    final_state: str | None
    events: tuple[_TestnetExecutionEventPayload, ...]
    blockers: tuple[str, ...]


def test_exchange_testnet_execution_cli_runs_hardened_dry_run_json(tmp_path: Path) -> None:
    config = tmp_path / "binance-x7-testnet-execution.yaml"
    config_text = "\n".join(_HARDENED_TESTNET_CONFIG_LINES)
    config.write_text(
        f"{config_text}\n",
        encoding="utf-8",
    )
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "testnet-execute",
        "--config",
        str(config),
        "--json",
    ]

    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    validation = subprocess.run(
        [sys.executable, "-m", "json.tool"],
        cwd=PROJECT_ROOT,
        input=result.stdout,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = _TestnetExecutionPayload.model_validate_json(result.stdout)

    assert result.returncode == 0, result.stderr
    assert validation.returncode == 0, validation.stderr
    assert payload.exchange == "binance"
    assert payload.trading_mode == "futures"
    assert payload.testnet is True
    assert payload.execution_ready is True
    assert payload.live_money_orders_enabled is False
    assert payload.live_exchange_observed is False
    assert payload.client_order_id.startswith("nfi-tn-")
    assert payload.submitted_order_id == "sim-1"
    assert payload.adapter_order_state == "filled"
    assert payload.final_state == "reconciled"
    assert payload.blockers == ()
    assert tuple(event.state for event in payload.events) == (
        "intent_created",
        "risk_checked",
        "submitted",
        "filled",
        "reconciled",
    )
    assert "local-test-secret" not in result.stdout
    assert "local-test-secret" not in result.stderr


def test_exchange_testnet_execution_cli_keeps_example_config_unsubmitted() -> None:
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "testnet-execute",
        "--config",
        "examples/futures-paper.yaml",
    ]

    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert "execution_ready=false" in result.stdout
    assert "live_money_orders_enabled=false" in result.stdout
    assert "submitted_order_id=none" in result.stdout
    assert "adapter_order_state=none" in result.stdout
    assert "TESTNET_PILOT_CREDENTIALS_MISSING" in result.stdout
