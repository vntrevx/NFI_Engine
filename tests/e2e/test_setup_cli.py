from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_setup_init_generates_valid_futures_testnet_config_without_stdout_secrets(
    tmp_path: Path,
) -> None:
    # Given: a non-interactive first-run setup command.
    config = tmp_path / "setup.yaml"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "setup",
        "init",
        "--config",
        str(config),
        "--exchange",
        "bybit",
        "--trading-mode",
        "futures",
        "--testnet",
        "--api-key",
        "cli-key",
        "--api-secret",
        "cli-secret",
        "--non-interactive",
    ]

    # When: the setup command writes the runtime config.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    validation_command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "validate",
        "--config",
        str(config),
    ]
    validation = subprocess.run(
        validation_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then: the config validates and command output stays redacted.
    assert result.returncode == 0, result.stderr
    assert validation.returncode == 0, validation.stderr
    assert "setup_config=" in result.stdout
    assert "trading_mode=futures" in result.stdout
    assert "intent=testnet" in result.stdout
    assert "duration_ms=" in result.stdout
    assert "cli-key" not in result.stdout
    assert "cli-secret" not in result.stdout
    assert "cli-key" not in result.stderr
    assert "cli-secret" not in result.stderr


def test_setup_init_blocks_live_mode_without_explicit_confirmation(tmp_path: Path) -> None:
    # Given: live mode without explicit live confirmation.
    config = tmp_path / "live.yaml"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "setup",
        "init",
        "--config",
        str(config),
        "--exchange",
        "bybit",
        "--trading-mode",
        "spot",
        "--live",
        "--api-key",
        "live-key",
        "--api-secret",
        "live-secret",
        "--non-interactive",
    ]

    # When: setup is requested.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: live trading still needs the existing explicit confirmation gate.
    assert result.returncode == 1
    assert "LIVE_TRADING_REQUIRES_CONFIRMATION" in result.stderr
    assert "live-key" not in result.stdout
    assert "live-secret" not in result.stdout
    assert not config.exists()
