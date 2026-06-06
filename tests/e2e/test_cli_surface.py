from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_cli_help_lists_operator_commands() -> None:
    # Given
    command: Final = ["uv", "run", "nfi-engine", "--help"]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    for command_name in (
        "config",
        "strategy",
        "data",
        "exchange",
        "db",
        "backtest",
        "paper-run",
        "serve",
    ):
        assert command_name in result.stdout


def test_cli_config_validate_succeeds_for_spot_paper_config() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "validate",
        "--config",
        "examples/spot-paper.yaml",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "valid" in result.stdout
    assert "trading_mode=spot" in result.stdout


def test_cli_expected_config_error_returns_typed_code() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "validate",
        "--config",
        "tests/fixtures/config/live-without-confirmation.yaml",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 1
    assert "LIVE_TRADING_REQUIRES_CONFIRMATION" in result.stderr


def test_cli_backtest_json_output_parses() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "backtest",
        "--config",
        "examples/spot-paper.yaml",
        "--timerange",
        "2026-01-01:2026-01-07",
        "--json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    pretty = subprocess.run(
        [sys.executable, "-m", "json.tool"],
        cwd=PROJECT_ROOT,
        input=result.stdout,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert pretty.returncode == 0, pretty.stderr
    assert '"summary"' in pretty.stdout


def test_cli_paper_run_reports_no_live_orders() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "paper-run",
        "--config",
        "examples/futures-paper.yaml",
        "--ticks",
        "tests/fixtures/ticks/btc_usdt_futures.jsonl",
        "--max-events",
        "3",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "processed_events=3" in result.stdout
    assert "live_orders=false" in result.stdout
