from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


class _ExchangeLifecycleOperationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    state: str


class _ExchangeLifecycleCliPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    exchange: str
    trading_mode: str
    testnet: bool
    live_exchange: bool
    preflight_blocked: bool
    deterministic_order_id: str
    operations: tuple[_ExchangeLifecycleOperationPayload, ...]
    funding_supported: bool
    leverage: str


def test_cli_exchange_lifecycle_smoke_outputs_safe_testnet_order_states() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "lifecycle",
        "smoke",
        "--config",
        "examples/futures-paper.yaml",
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
    payload = _ExchangeLifecycleCliPayload.model_validate_json(result.stdout)

    # Then
    assert result.returncode == 0, result.stderr
    assert validation.returncode == 0, validation.stderr
    assert payload.exchange == "bybit"
    assert payload.trading_mode == "futures"
    assert payload.testnet is True
    assert payload.live_exchange is False
    assert payload.preflight_blocked is False
    assert payload.deterministic_order_id == "sim-1"
    assert payload.leverage == "3"
    assert payload.funding_supported is True
    assert {operation.name: operation.state for operation in payload.operations} == {
        "create_order": "open",
        "fetch_order": "open",
        "cancel_order": "canceled",
        "partial_fill_report": "partially_filled",
        "rejected_report": "rejected",
    }


def test_cli_exchange_lifecycle_blocks_live_exchange_config_before_order_surface() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "lifecycle",
        "smoke",
        "--config",
        "tests/fixtures/config/live-real-orders.yaml",
        "--json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 1
    assert result.stdout == ""
    assert "EXCHANGE_LIFECYCLE_PREFLIGHT_BLOCKED" in result.stderr
    assert "LIVE_TRADING_OUT_OF_SCOPE" in result.stderr
    assert "EXCHANGE_TESTNET_REQUIRED" in result.stderr
