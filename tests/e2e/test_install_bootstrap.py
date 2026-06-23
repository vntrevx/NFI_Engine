from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_package_scripts_offer_npm_and_bun_bootstrap_commands() -> None:
    package_path = PROJECT_ROOT / "package.json"

    json_check = subprocess.run(
        [sys.executable, "-m", "json.tool", str(package_path)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    package_text = package_path.read_text(encoding="utf-8")

    assert json_check.returncode == 0, json_check.stderr
    assert '"nfi:install": "bash scripts/install.sh --yes --paper --testnet"' in package_text
    assert (
        '"nfi:install:dry-run": "bash scripts/install.sh --yes --paper --testnet --dry-run"'
        in package_text
    )
    assert '"nfi:uninstall": "bash scripts/uninstall.sh --yes"' in package_text
    assert (
        '"nfi:uninstall:purge:dry-run": "bash scripts/uninstall.sh --purge --yes --dry-run"'
        in package_text
    )
    assert '"nfi:pi4:rc-check": "bash scripts/pi4_rc_profile.sh"' in package_text
    assert '"dependencies"' not in package_text


def test_install_script_missing_uv_prints_actionable_remediation(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    empty_path = tmp_path / "empty-path"
    empty_path.mkdir()
    environment = os.environ.copy()
    environment["PATH"] = str(empty_path)
    command: Final = [
        "/bin/bash",
        "scripts/install.sh",
        "--yes",
        "--paper",
        "--testnet",
        "--runtime-dir",
        str(runtime_dir),
        "--dry-run",
    ]

    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode != 0
    assert "INSTALL_MISSING_COMMAND: uv" in result.stderr
    assert "install_hint=Install uv from https://docs.astral.sh/uv/" in result.stderr
    assert "python3" in result.stderr
    assert not runtime_dir.exists()


def test_final_smoke_records_install_and_uninstall_dry_run_matrix() -> None:
    script = (PROJECT_ROOT / "scripts/final_smoke.sh").read_text(encoding="utf-8")

    assert "final-install-dry-run.txt" in script
    assert "final-uninstall-safe-dry-run.txt" in script
    assert "final-uninstall-purge-dry-run.txt" in script
    assert "final-x7-strategy-inspect.json" in script
    assert "final-x7-forbidden-runtime-modules.txt" in script
    assert "final-release-wording-scan.txt" in script
    assert "bash scripts/install.sh --yes --paper --testnet --dry-run" in script
    assert "bash scripts/uninstall.sh --yes --dry-run" in script
    assert "bash scripts/uninstall.sh --purge --yes --dry-run" in script
    assert "scripts/release_wording_scan.py" in script
    assert "nfi_engine.strategy.nfi_x7:X7NativeStrategy" in script


def test_final_smoke_records_protected_dashboard_auth_boundary() -> None:
    # Given: the final smoke script used as the Docker first-run release gate.
    script = (PROJECT_ROOT / "scripts/final_smoke.sh").read_text(encoding="utf-8")

    # When/Then: it records both the unauthenticated denial and authenticated success.
    assert "final-dashboard-snapshot-unauthenticated.status" in script
    assert "final-dashboard-snapshot-unauthenticated.json" in script
    expected_denial_check: Final = (
        '[[ "${unauth_status}" == "401" || "${unauth_status}" == "403" ]]'
    )
    assert expected_denial_check in script
    assert "Authorization: Bearer ${api_token}" in script
    assert "final-dashboard-snapshot.json" in script
