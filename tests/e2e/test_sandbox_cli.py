from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

from nfi_engine.compat import NfiCompatibilityReport

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_sandbox_cli_allows_nfi_shape_strategy() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "sandbox",
        "check",
        "--strategy",
        "tests.fixtures.strategies.nfi_shape:NFISmokeStrategy",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "sandbox_passed=true" in result.stdout


def test_sandbox_cli_writes_clean_room_compatibility_report(tmp_path: Path) -> None:
    # Given
    output_path = tmp_path / "compat.json"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "sandbox",
        "check",
        "--strategy",
        "tests.fixtures.strategies.nfi_shape:NFISmokeStrategy",
        "--output",
        str(output_path),
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    payload = NfiCompatibilityReport.model_validate_json(output_path.read_text(encoding="utf-8"))

    # Then
    assert result.returncode == 0, result.stderr
    assert payload.compatible is True
    assert payload.full_x7_parity is False
    assert "populate_entry_trend" in payload.supported_callbacks
    assert "informative_pairs" in payload.partial_callbacks
    assert "full_x7_strategy_import" in payload.excluded_surfaces


def test_sandbox_cli_blocks_environment_reading_strategy() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "sandbox",
        "check",
        "--strategy",
        "tests.fixtures.strategies.unsafe:EnvReadingStrategy",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 1
    assert "SANDBOX_VIOLATION" in result.stderr
    assert "env_read" in result.stderr
