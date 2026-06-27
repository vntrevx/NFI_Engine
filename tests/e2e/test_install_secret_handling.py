from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_install_script_accepts_env_credentials_without_output_leaks(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    env = os.environ.copy()
    env.update(
        {
            "NFI_ENGINE_SETUP_API_KEY": "install-key",
            "NFI_ENGINE_SETUP_API_SECRET": "install-secret",
            "NFI_ENGINE_SETUP_PASSPHRASE": "install-passphrase",
        },
    )
    command: Final = [
        "bash",
        "scripts/install.sh",
        "--yes",
        "--paper",
        "--testnet",
        "--runtime-dir",
        str(runtime_dir),
        "--exchange",
        "bitget",
        "--dry-run",
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "intent=testnet" in result.stdout
    assert "install-key" not in result.stdout
    assert "install-secret" not in result.stdout
    assert "install-passphrase" not in result.stdout
    assert not tuple(runtime_dir.glob("setup-credentials.*"))


def test_install_script_rejects_secret_command_arguments(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    command: Final = [
        "bash",
        "scripts/install.sh",
        "--yes",
        "--paper",
        "--runtime-dir",
        str(runtime_dir),
        "--api-secret",
        "unsafe-argv-secret",
        "--dry-run",
    ]

    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    assert result.returncode != 0
    assert "INSTALL_SECRET_ARGUMENT_REJECTED" in result.stderr
    assert "unsafe-argv-secret" not in result.stderr
    assert not runtime_dir.exists()
