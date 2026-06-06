from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_paper_run_cli_writes_event_jsonl(tmp_path: Path) -> None:
    # Given
    events_path = tmp_path / "paper-events.jsonl"
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
        "5",
        "--events",
        str(events_path),
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    content = events_path.read_text(encoding="utf-8")
    assert "bot_started" in content
    assert "bot_stopped" in content


def test_config_show_redacts_secret_fixture() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "show",
        "--config",
        "tests/fixtures/config/with-secret.yaml",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "fixture-secret-value" not in result.stdout
    assert "REDACTED" in result.stdout


def test_logs_explain_reads_event_file() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "logs",
        "explain",
        "CONFIG_VALIDATION_ERROR",
        "--events",
        "tests/fixtures/events/config_validation_error.jsonl",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "CONFIG_VALIDATION_ERROR" in result.stdout
    assert "correlation_id=corr-config-fixture" in result.stdout
    assert "safe_summary=" in result.stdout
    assert "report_hint=" in result.stdout
