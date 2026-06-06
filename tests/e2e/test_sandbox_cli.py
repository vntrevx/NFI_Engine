from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

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
