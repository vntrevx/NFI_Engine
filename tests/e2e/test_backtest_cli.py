from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_backtest_cli_writes_json_summary_when_spot_config_is_valid(tmp_path: Path) -> None:
    # Given
    output_path = tmp_path / "spot-backtest.json"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "backtest",
        "--config",
        "examples/spot-paper.yaml",
        "--timerange",
        "2026-01-01:2026-01-07",
        "--output",
        str(output_path),
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "summary.total_trades=" in result.stdout
    output = output_path.read_text(encoding="utf-8")
    assert '"trades"' in output
    assert '"equity_curve"' in output
    assert '"summary"' in output
    assert '"config_digest"' in output
    assert '"strategy"' in output
    assert '"timeline"' in output
    assert '"payload_bytes"' in output
    assert '"simulator"' not in output


def test_backtest_cli_blocks_futures_config_with_unsafe_liquidation_buffer() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "backtest",
        "--config",
        "tests/fixtures/config/futures-liquidation-risk.yaml",
        "--timerange",
        "2026-01-01:2026-01-07",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 1
    assert "LIQUIDATION_BUFFER_VIOLATION" in result.stderr


def test_backtest_cli_records_simulator_metadata_only_when_scenario_enabled(
    tmp_path: Path,
) -> None:
    # Given
    output_path = tmp_path / "scenario-backtest.json"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "backtest",
        "--config",
        "examples/spot-paper.yaml",
        "--timerange",
        "2026-01-01:2026-01-07",
        "--simulator-scenario",
        "tests/fixtures/simulator/partial_fill_latency.yaml",
        "--output",
        str(output_path),
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    payload = output_path.read_text(encoding="utf-8")
    assert '"simulator"' in payload
    assert '"scenario_hash"' in payload
    assert '"seed": 4242' in payload
