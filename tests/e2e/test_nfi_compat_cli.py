from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_nfi_compat_cli_reports_clean_room_fixture_support() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "compat",
        "nfi-check",
        "--strategy",
        "tests.fixtures.strategies.nfi_shape:NFISmokeStrategy",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "compatible=true" in result.stdout
    assert "full_x7_parity=false" in result.stdout
    assert "4de91e1928f6203694733ffb9899023ef62fd7fc" in result.stdout


def test_source_tree_does_not_vendor_upstream_x7() -> None:
    # Given
    command: Final = [
        "rg",
        "-n",
        "NostalgiaForInfinityX7 by iterativ|long_normal_mode_tags|Referral Links",
        "src",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 1
    assert result.stdout == ""
