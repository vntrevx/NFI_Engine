from __future__ import annotations

import subprocess
from io import BytesIO
from pathlib import Path
from typing import Final
from zipfile import ZipFile

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.config.models import ApiSettings, ExchangeSettings, RuntimeSettings

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
LOCAL_BEARER: Final = "task-25-local-bearer"


def test_backup_create_and_verify_cli() -> None:
    # Given: a target backup path under evidence.
    output = PROJECT_ROOT / ".omo/evidence/task-25-cli-backup.zip"
    output.unlink(missing_ok=True)
    create_command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "backup",
        "create",
        "--config",
        "examples/futures-paper.yaml",
        "--output",
        str(output),
    ]
    verify_command: Final = ["uv", "run", "nfi-engine", "backup", "verify", str(output)]

    # When: backup create and verify commands run.
    create = subprocess.run(
        create_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    verify = subprocess.run(
        verify_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then: the archive exists and verification reports a valid redacted manifest.
    assert create.returncode == 0, create.stderr
    assert verify.returncode == 0, verify.stderr
    assert output.exists()
    assert "backup_created=true" in create.stdout
    assert "manifest_valid=true" in verify.stdout
    assert "redacted=true" in verify.stdout


def test_backup_restore_dry_run_cli() -> None:
    # Given: an existing backup archive.
    output = PROJECT_ROOT / ".omo/evidence/task-25-cli-restore.zip"
    create_command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "backup",
        "create",
        "--config",
        "examples/futures-paper.yaml",
        "--output",
        str(output),
    ]
    restore_command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "backup",
        "restore",
        "--dry-run",
        str(output),
    ]
    subprocess.run(
        create_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    # When: restore is run as dry-run.
    restore = subprocess.run(
        restore_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then: restore reports a plan without applying changes.
    assert restore.returncode == 0, restore.stderr
    assert "restore_plan=backup" in restore.stdout
    assert "apply=false" in restore.stdout
    assert "manifest_valid=true" in restore.stdout


@pytest.mark.anyio
async def test_diagnostic_bundle_export_is_available_from_frontend_and_api() -> None:
    # Given: a token-protected local app with exchange and API secrets.
    settings = RuntimeSettings(
        exchange=ExchangeSettings.model_validate(
            {"api_key": "bundle-key", "api_secret": "bundle-secret"},
        ),
        api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}),
    )
    headers = {"Authorization": f"Bearer {LOCAL_BEARER}"}

    async with AsyncClient(
        transport=ASGITransport(app=create_app(settings=settings)),
        base_url="http://testserver",
    ) as client:
        # When: the frontend page advertises export and the REST zip is downloaded.
        login = await client.post("/api/v1/session/login", headers=headers)
        page = await client.get("/logs")
        bundle = await client.get("/api/v1/reports/support-bundle.zip", headers=headers)

    # Then: the diagnostic bundle is redacted and includes manifest checksums.
    assert login.status_code == 200
    assert page.status_code == 200
    assert "/api/v1/reports/support-bundle.zip" in page.text
    assert bundle.status_code == 200
    with ZipFile(BytesIO(bundle.content)) as archive:
        names = set(archive.namelist())
        manifest = archive.read("manifest.json").decode("utf-8")
        merged = "\n".join(archive.read(name).decode("utf-8") for name in sorted(names))
    assert {"config.json", "logs.json", "manifest.json"} <= names
    assert '"checksums"' in manifest
    assert '"config.json"' in manifest
    assert "REDACTED" in merged
    assert "bundle-key" not in merged
    assert "bundle-secret" not in merged
    assert LOCAL_BEARER not in merged
