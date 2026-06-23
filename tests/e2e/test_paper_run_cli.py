from __future__ import annotations

import subprocess
from pathlib import Path


def test_paper_run_cli_writes_timeline_output(tmp_path: Path) -> None:
    # Given
    timeline_path = tmp_path / "paper-timeline.json"
    command = [
        "uv",
        "run",
        "nfi-engine",
        "paper-run",
        "--config",
        "examples/futures-paper.yaml",
        "--ticks",
        "tests/fixtures/ticks/btc_usdt_futures.jsonl",
        "--max-events",
        "5",
        "--timeline-output",
        str(timeline_path),
    ]

    # When
    result = subprocess.run(command, check=False, capture_output=True, text=True)

    # Then
    assert result.returncode == 0
    payload = timeline_path.read_text(encoding="utf-8")
    assert '"surface": "paper"' in payload
    assert '"payload_bytes"' in payload
    assert '"entry_signals": 1' in payload


def test_paper_run_cli_processes_tick_fixture() -> None:
    # Given
    command = [
        "uv",
        "run",
        "nfi-engine",
        "paper-run",
        "--config",
        "examples/futures-paper.yaml",
        "--ticks",
        "tests/fixtures/ticks/btc_usdt_futures.jsonl",
        "--max-events",
        "5",
    ]

    # When
    result = subprocess.run(command, check=False, capture_output=True, text=True)

    # Then
    assert result.returncode == 0
    assert "processed_events=5" in result.stdout
    assert "live_orders=false" in result.stdout


def test_paper_run_cli_rejects_malformed_tick_stream() -> None:
    # Given
    command = [
        "uv",
        "run",
        "nfi-engine",
        "paper-run",
        "--config",
        "examples/futures-paper.yaml",
        "--ticks",
        "tests/fixtures/ticks/malformed.jsonl",
        "--max-events",
        "5",
    ]

    # When
    result = subprocess.run(command, check=False, capture_output=True, text=True)

    # Then
    assert result.returncode == 1
    assert "TICK_PARSE_ERROR" in result.stderr
