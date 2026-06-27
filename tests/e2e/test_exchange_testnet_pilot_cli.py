from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


class _TestnetPilotPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    exchange: str
    trading_mode: str
    testnet: bool
    pilot_ready: bool
    live_money_orders_enabled: bool
    sample_client_order_id: str
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
    assert "TESTNET_PILOT_CREDENTIALS_MISSING" in result.stdout
