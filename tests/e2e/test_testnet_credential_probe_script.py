from __future__ import annotations

import stat
import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
PRIORITY_EXCHANGES: Final = ("binance", "bybit", "okx", "bitget")


def test_testnet_credential_probe_init_template_writes_owner_only_files(
    tmp_path: Path,
) -> None:
    credentials_dir = tmp_path / "secrets"
    command: Final = [
        "bash",
        "scripts/testnet_credential_probe.sh",
        "--credentials-dir",
        str(credentials_dir),
        "--init-template",
    ]

    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert stat.S_IMODE(credentials_dir.stat().st_mode) == 0o700
    for exchange in PRIORITY_EXCHANGES:
        credentials_file = credentials_dir / f"testnet-{exchange}.env"
        credentials_text = credentials_file.read_text(encoding="utf-8")
        assert stat.S_IMODE(credentials_file.stat().st_mode) == 0o600
        assert f"template=created exchange={exchange}" in result.stdout
        assert "api_key=" in credentials_text
        assert "api_secret=" in credentials_text
    assert "passphrase=" in (credentials_dir / "testnet-okx.env").read_text(encoding="utf-8")
    assert "passphrase=" in (credentials_dir / "testnet-bitget.env").read_text(encoding="utf-8")


def test_testnet_credential_probe_empty_templates_stay_blocked_no_key(
    tmp_path: Path,
) -> None:
    credentials_dir = tmp_path / "secrets"
    init_command: Final = [
        "bash",
        "scripts/testnet_credential_probe.sh",
        "--credentials-dir",
        str(credentials_dir),
        "--init-template",
    ]
    probe_command: Final = [
        "bash",
        "scripts/testnet_credential_probe.sh",
        "--credentials-dir",
        str(credentials_dir),
    ]

    init_result = subprocess.run(
        init_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    result = subprocess.run(
        probe_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert init_result.returncode == 0, init_result.stderr
    assert result.returncode == 0, result.stderr
    assert result.stdout.count("credential_status=blocked-no-key") == len(PRIORITY_EXCHANGES)
    assert result.stdout.count("credential_non_empty_fields=none") == len(PRIORITY_EXCHANGES)
    assert result.stdout.count("real_testnet_action=blocked-no-key") == len(PRIORITY_EXCHANGES)
    for exchange in PRIORITY_EXCHANGES:
        assert f"credential_file={credentials_dir}/testnet-{exchange}.env" in result.stdout


def test_testnet_credential_probe_redacts_present_sample_fields(tmp_path: Path) -> None:
    credentials_dir = tmp_path / "secrets"
    credentials_dir.mkdir()
    for exchange in PRIORITY_EXCHANGES:
        credentials_file = credentials_dir / f"testnet-{exchange}.env"
        if exchange in {"okx", "bitget"}:
            credentials_text = "\n".join(
                (
                    f"api_key=sample-{exchange}-key",
                    f"api_secret=sample-{exchange}-secret",
                    f"passphrase=sample-{exchange}-pass",
                    "",
                ),
            )
        else:
            credentials_text = "\n".join(
                (
                    f"api_key=sample-{exchange}-key",
                    f"api_secret=sample-{exchange}-secret",
                    "",
                ),
            )
        credentials_file.write_text(credentials_text, encoding="utf-8")
        credentials_file.chmod(0o600)
    command: Final = [
        "bash",
        "scripts/testnet_credential_probe.sh",
        "--credentials-dir",
        str(credentials_dir),
    ]

    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    assert result.returncode == 0, result.stderr
    assert result.stdout.count("credential_status=present") == len(PRIORITY_EXCHANGES)
    assert result.stdout.count("setup\tsecrets=redacted") == len(PRIORITY_EXCHANGES)
    assert result.stdout.count("real_testnet_action=blocked-pilot") == len(PRIORITY_EXCHANGES)
    assert "sample-binance-key" not in result.stdout
    assert "sample-bybit-secret" not in result.stdout
    assert "sample-okx-pass" not in result.stdout
    assert "sample-bitget-pass" not in result.stdout
