from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_cli_help_boots_when_project_is_installed() -> None:
    # Given
    command: Final = ["uv", "run", "nfi-engine", "--help"]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "Usage:" in result.stdout
    assert "nfi-engine" in result.stdout
