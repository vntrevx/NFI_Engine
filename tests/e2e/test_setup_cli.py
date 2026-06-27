from __future__ import annotations

import stat
import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_setup_init_generates_valid_futures_testnet_config_without_stdout_secrets(
    tmp_path: Path,
) -> None:
    # Given: a non-interactive first-run setup command.
    config = tmp_path / "setup.yaml"
    credentials_file = tmp_path / "credentials.env"
    credentials_file.write_text("api_key=cli-key\napi_secret=cli-secret\n", encoding="utf-8")
    credentials_file.chmod(0o600)
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
        "--credentials-file",
        str(credentials_file),
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


def test_setup_init_accepts_exchange_specific_credentials_without_stdout_leaks(
    tmp_path: Path,
) -> None:
    config = tmp_path / "bitget.yaml"
    credentials_file = tmp_path / "bitget-credentials.env"
    credentials_file.write_text(
        "api_key=bitget-cli-key\napi_secret=bitget-cli-secret\npassphrase=bitget-cli-passphrase\n",
        encoding="utf-8",
    )
    credentials_file.chmod(0o600)
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "setup",
        "init",
        "--config",
        str(config),
        "--exchange",
        "bitget",
        "--trading-mode",
        "futures",
        "--testnet",
        "--credentials-file",
        str(credentials_file),
        "--non-interactive",
    ]

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
    config_text = config.read_text(encoding="utf-8")

    assert result.returncode == 0, result.stderr
    assert validation.returncode == 0, validation.stderr
    assert "passphrase: 'bitget-cli-passphrase'" in config_text
    assert "bitget-cli-passphrase" not in result.stdout
    assert "bitget-cli-passphrase" not in result.stderr


def test_setup_init_rejects_secret_command_arguments_without_echoing_values(
    tmp_path: Path,
) -> None:
    # Given: a direct setup command carries a secret in argv.
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
        "--api-secret",
        "unsafe-cli-secret",
        "--non-interactive",
    ]

    # When: the setup CLI parses the command.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: it rejects the secret-bearing argument without echoing the value.
    assert result.returncode == 1
    assert "SETUP_SECRET_ARGUMENT_REJECTED" in result.stderr
    assert "unsafe-cli-secret" not in result.stdout
    assert "unsafe-cli-secret" not in result.stderr
    assert not config.exists()


def test_setup_init_accepts_secure_credentials_file_without_stdout_leaks(
    tmp_path: Path,
) -> None:
    # Given: exchange credentials are stored in an owner-only key/value file.
    config = tmp_path / "bitget.yaml"
    credentials_file = tmp_path / "credentials.env"
    credentials_file.write_text(
        "api_key=file-key\napi_secret=file-secret\npassphrase=file-passphrase\n",
        encoding="utf-8",
    )
    credentials_file.chmod(0o600)
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "setup",
        "init",
        "--config",
        str(config),
        "--exchange",
        "bitget",
        "--trading-mode",
        "futures",
        "--testnet",
        "--credentials-file",
        str(credentials_file),
        "--non-interactive",
    ]

    # When: setup reads the file instead of secret-bearing process arguments.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    config_text = config.read_text(encoding="utf-8")

    # Then: the config contains the values, but command output stays redacted.
    assert result.returncode == 0, result.stderr
    assert stat.S_IMODE(credentials_file.stat().st_mode) == 0o600
    assert "api_key: 'file-key'" in config_text
    assert "api_secret: 'file-secret'" in config_text
    assert "passphrase: 'file-passphrase'" in config_text
    assert "file-secret" not in result.stdout
    assert "file-passphrase" not in result.stdout
    assert "file-secret" not in result.stderr
    assert "file-passphrase" not in result.stderr


def test_setup_init_rejects_world_readable_credentials_file(tmp_path: Path) -> None:
    # Given: a credential file is readable by other local users.
    config = tmp_path / "bitget.yaml"
    credentials_file = tmp_path / "credentials.env"
    credentials_file.write_text("api_secret=unsafe-file-secret\n", encoding="utf-8")
    credentials_file.chmod(0o644)
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "setup",
        "init",
        "--config",
        str(config),
        "--exchange",
        "bitget",
        "--trading-mode",
        "futures",
        "--testnet",
        "--credentials-file",
        str(credentials_file),
        "--non-interactive",
    ]

    # When: setup attempts to load it.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: it fails before writing a runtime config.
    assert result.returncode == 1
    assert "SETUP_CREDENTIALS_FILE_UNSAFE_MODE" in result.stderr
    assert "unsafe-file-secret" not in result.stdout
    assert "unsafe-file-secret" not in result.stderr
    assert not config.exists()


def test_setup_init_blocks_live_mode_without_explicit_confirmation(tmp_path: Path) -> None:
    # Given: live mode without explicit live confirmation.
    config = tmp_path / "live.yaml"
    credentials_file = tmp_path / "live-credentials.env"
    credentials_file.write_text("api_key=live-key\napi_secret=live-secret\n", encoding="utf-8")
    credentials_file.chmod(0o600)
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
        "--credentials-file",
        str(credentials_file),
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
