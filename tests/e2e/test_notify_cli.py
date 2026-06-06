from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_notify_cli_jsonl_writes_smoke_event(tmp_path: Path) -> None:
    # Given
    output = tmp_path / "notify.jsonl"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "notify",
        "test",
        "--config",
        "examples/futures-paper.yaml",
        "--channel",
        "jsonl",
        "--message",
        "smoke",
        "--output",
        str(output),
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "notification_failed=false" in result.stdout
    assert "smoke" in output.read_text(encoding="utf-8")


def test_notify_cli_webhook_failure_is_nonfatal() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "notify",
        "test",
        "--config",
        "tests/fixtures/config/webhook-timeout.yaml",
        "--channel",
        "webhook",
        "--message",
        "timeout-smoke",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "notification_failed=true" in result.stdout
    assert "failure_code=" in result.stdout
