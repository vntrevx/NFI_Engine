from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_profile_list_cli_shows_builtin_profiles() -> None:
    # Given: the operator CLI.
    command: Final = ["uv", "run", "nfi-engine", "profile", "list"]

    # When: profiles are listed.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: every required profile is visible.
    assert result.returncode == 0, result.stderr
    for profile_name in ("local-paper", "bybit-testnet", "backtest-only", "readonly-debug"):
        assert profile_name in result.stdout


def test_preflight_cli_passes_for_bybit_testnet_fixture() -> None:
    # Given: the Bybit futures paper fixture.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "preflight",
        "check",
        "--profile",
        "bybit-testnet",
        "--config",
        "examples/futures-paper.yaml",
    ]

    # When: preflight runs.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the CLI emits a pass summary and typed check codes.
    assert result.returncode == 0, result.stderr
    assert "PREFLIGHT_PASSED" in result.stdout
    assert "PROFILE_COMPATIBLE" in result.stdout
    assert "DOCKER_VOLUMES_READY" in result.stdout


def test_preflight_cli_blocks_public_api_bind() -> None:
    # Given: a config with public API bind.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "preflight",
        "check",
        "--profile",
        "local-paper",
        "--config",
        "tests/fixtures/config/api-public-bind.yaml",
    ]

    # When: preflight runs.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the blocking code is visible and the process fails.
    assert result.returncode == 1
    assert "PREFLIGHT_BLOCKED" in result.stdout
    assert "PUBLIC_BIND_NOT_ALLOWED" in result.stdout
