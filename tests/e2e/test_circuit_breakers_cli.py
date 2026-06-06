from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_circuit_breaker_simulate_daily_loss_reports_halt() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "circuit-breaker",
        "simulate",
        "--config",
        "tests/fixtures/config/daily-loss-limit.yaml",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "trading_halted=true" in result.stdout
    assert "breaker=daily_loss" in result.stdout


def test_paper_run_blocks_new_orders_after_stale_data_breaker() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "paper-run",
        "--config",
        "tests/fixtures/config/stale-data-breaker.yaml",
        "--ticks",
        "tests/fixtures/ticks/stale_stream.jsonl",
        "--max-events",
        "10",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "created_trades=1" in result.stdout
    assert "trading_halted=true" in result.stdout
    assert "breaker=stale_data" in result.stdout
    assert "new_orders_blocked=true" in result.stdout
