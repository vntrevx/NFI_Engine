from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_exchange_reconcile_cli_reports_matching_state() -> None:
    # Given: a matching local/exchange fixture.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "reconcile",
        "--config",
        "examples/futures-paper.yaml",
        "--dry-run",
        "--fixture",
        "tests/fixtures/exchange/reconcile_match.json",
    ]

    # When: reconciliation runs through the operator CLI.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the process exits cleanly with zero mismatches.
    assert result.returncode == 0, result.stderr
    assert "apply=false" in result.stdout
    assert "mismatch_count=0" in result.stdout
    assert "trading_halted=false" in result.stdout


def test_exchange_reconcile_cli_blocks_mismatched_state() -> None:
    # Given: a fixture with position and order drift.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "reconcile",
        "--config",
        "examples/futures-paper.yaml",
        "--dry-run",
        "--fixture",
        "tests/fixtures/exchange/reconcile_mismatch.json",
    ]

    # When: reconciliation runs through the operator CLI.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the CLI reports safety drift and does not apply actions.
    assert result.returncode == 1
    assert "apply=false" in result.stdout
    assert "trading_halted=true" in result.stdout
    assert "POSITION_MISMATCH" in result.stdout


def test_preflight_cli_blocks_when_startup_reconciliation_is_required() -> None:
    # Given: a config requiring startup recovery reconciliation.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "preflight",
        "check",
        "--profile",
        "bybit-testnet",
        "--config",
        "tests/fixtures/config/reconcile-required.yaml",
    ]

    # When: preflight runs.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: startup recovery blocks unsafe operation.
    assert result.returncode == 1
    assert "PREFLIGHT_BLOCKED" in result.stdout
    assert "RECONCILIATION_REQUIRED" in result.stdout
