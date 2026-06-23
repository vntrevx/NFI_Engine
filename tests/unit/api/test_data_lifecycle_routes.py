from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict

from nfi_engine.api.app import create_app
from nfi_engine.api.auth import ApiErrorResponse
from nfi_engine.api.data_lifecycle_models import (
    DataLifecycleExportResponse,
    DataLifecycleFootprintResponse,
    DataLifecyclePruneReceiptResponse,
)
from nfi_engine.api.errors import ApiErrorCode
from nfi_engine.config.models import ApiSettings, DatabaseSettings, RuntimeSettings, UiSettings
from nfi_engine.maintenance.data_lifecycle import (
    DATA_LIFECYCLE_CONFIRM_SCOPE,
    DATA_LIFECYCLE_CONFIRMATION_REQUIRED,
)

if TYPE_CHECKING:
    from fastapi import FastAPI

LOCAL_BEARER = "local-test-bearer"


class ErrorEnvelope(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    detail: ApiErrorResponse


class SessionPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    role: str
    csrf_token: str
    expires_at: datetime


@pytest.mark.anyio
async def test_data_lifecycle_footprint_and_export_are_redacted(tmp_path: Path) -> None:
    # Given: an authorized operator client with temp runtime data.
    settings = _settings(tmp_path)
    _runtime_file(tmp_path, "engine.sqlite3", b"sqlite")
    _runtime_file(tmp_path, "logs/engine.log", b"log")
    _runtime_file(tmp_path, "backups/backup.zip", b"backup")
    _runtime_file(tmp_path, "support-bundles/support.zip", b"support")
    _runtime_file(tmp_path, "evidence/operator.json", b"evidence")
    client = _client(create_app(settings=settings, config_path=tmp_path / "config.yaml"))

    # When: footprint and export endpoints are read.
    footprint = await client.get("/api/v1/data-lifecycle/footprint", headers=_auth_headers())
    export = await client.get("/api/v1/data-lifecycle/export", headers=_auth_headers())
    footprint_payload = DataLifecycleFootprintResponse.model_validate_json(footprint.content)
    export_payload = DataLifecycleExportResponse.model_validate_json(export.content)
    merged = export.text

    # Then: category totals are observable and secrets do not leak.
    assert footprint.status_code == 200
    assert footprint_payload.total_bytes > 0
    assert {category.name for category in footprint_payload.categories} == {
        "sqlite",
        "logs",
        "backups",
        "support_bundles",
        "evidence",
    }
    assert export.status_code == 200
    assert export_payload.receipt_id.startswith("data-export-")
    assert "operator-token-fixture" not in merged
    assert "https://hooks.example.invalid/raw-token" not in merged


@pytest.mark.anyio
async def test_data_lifecycle_prune_requires_csrf_and_preview_token(tmp_path: Path) -> None:
    # Given: a logged-in operator and a safe temp runtime artifact.
    client = _client(create_app(settings=_settings(tmp_path), config_path=tmp_path / "config.yaml"))
    session = await _login(client)
    old_log = _runtime_file(tmp_path, "logs/old.log", b"old")

    # When: prune is called through dry-run, missing CSRF, malformed, and apply paths.
    dry_run = await client.post(
        "/api/v1/data-lifecycle/prune",
        headers=_csrf_headers(session),
        json={"dry_run": True, "apply": False, "retention_days": 0},
    )
    dry_run_payload = DataLifecyclePruneReceiptResponse.model_validate_json(dry_run.content)
    missing_csrf = await client.post(
        "/api/v1/data-lifecycle/prune",
        headers=_auth_headers(),
        json={"dry_run": True, "apply": False},
    )
    malformed = await client.post(
        "/api/v1/data-lifecycle/prune",
        headers=_csrf_headers(session),
        json={"dry_run": "yes", "retention_days": "now"},
    )
    apply_without_token = await client.post(
        "/api/v1/data-lifecycle/prune",
        headers=_csrf_headers(session),
        json={
            "dry_run": False,
            "apply": True,
            "retention_days": 0,
            "confirm_scope": DATA_LIFECYCLE_CONFIRM_SCOPE,
        },
    )
    apply_without_confirmation = await client.post(
        "/api/v1/data-lifecycle/prune",
        headers=_csrf_headers(session),
        json={
            "dry_run": False,
            "apply": True,
            "retention_days": 0,
            "preview_token": dry_run_payload.preview_token,
        },
    )
    csrf_error = ErrorEnvelope.model_validate_json(missing_csrf.content)
    blocked_payload = DataLifecyclePruneReceiptResponse.model_validate_json(
        apply_without_token.content,
    )
    confirmation_payload = DataLifecyclePruneReceiptResponse.model_validate_json(
        apply_without_confirmation.content,
    )

    # Then: only preview is accepted and mutation requires the shared write gates.
    assert dry_run.status_code == 200
    assert dry_run_payload.accepted is True
    assert dry_run_payload.mutation_applied is False
    assert dry_run_payload.preview_token != ""
    assert missing_csrf.status_code == 403
    assert csrf_error.detail.code is ApiErrorCode.CSRF_TOKEN_REQUIRED
    assert malformed.status_code == 422
    assert apply_without_token.status_code == 200
    assert blocked_payload.accepted is False
    assert "preview_token_required" in blocked_payload.blocked_reasons
    assert apply_without_confirmation.status_code == 200
    assert confirmation_payload.accepted is False
    assert DATA_LIFECYCLE_CONFIRMATION_REQUIRED in confirmation_payload.blocked_reasons
    assert old_log.exists()

    successful_apply = await client.post(
        "/api/v1/data-lifecycle/prune",
        headers=_csrf_headers(session),
        json={
            "dry_run": False,
            "apply": True,
            "retention_days": 0,
            "preview_token": dry_run_payload.preview_token,
            "confirm_scope": DATA_LIFECYCLE_CONFIRM_SCOPE,
        },
    )
    apply_payload = DataLifecyclePruneReceiptResponse.model_validate_json(successful_apply.content)

    assert successful_apply.status_code == 200
    assert apply_payload.accepted is True
    assert apply_payload.mutation_applied is True
    assert apply_payload.deleted_count == 1
    assert not old_log.exists()


@pytest.mark.anyio
async def test_data_lifecycle_prune_is_blocked_in_read_only_mode(tmp_path: Path) -> None:
    # Given: a read-only console session.
    client = _client(
        create_app(
            settings=_settings(tmp_path, read_only=True),
            config_path=tmp_path / "config.yaml",
        ),
    )
    session = await _login(client)

    # When: inspection and prune are requested.
    footprint = await client.get("/api/v1/data-lifecycle/footprint", headers=_auth_headers())
    prune = await client.post(
        "/api/v1/data-lifecycle/prune",
        headers=_csrf_headers(session),
        json={"dry_run": True, "apply": False},
    )
    error = ErrorEnvelope.model_validate_json(prune.content)

    # Then: read-only mode allows inspection but blocks write-router actions.
    assert footprint.status_code == 200
    assert prune.status_code == 403
    assert error.detail.code is ApiErrorCode.READONLY_ACTION_BLOCKED


def _settings(root: Path, *, read_only: bool = False) -> RuntimeSettings:
    return RuntimeSettings(
        database=DatabaseSettings(url=f"sqlite+aiosqlite:///{root / 'engine.sqlite3'}"),
        api=ApiSettings(
            auth_token=LOCAL_BEARER,
            session_ttl_seconds=1800,
        ),
        ui=UiSettings(read_only=read_only),
    )


def _runtime_file(root: Path, relative: str, data: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {LOCAL_BEARER}"}


def _csrf_headers(session: SessionPayload) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {LOCAL_BEARER}",
        "x-nfi-csrf-token": session.csrf_token,
    }


async def _login(client: AsyncClient) -> SessionPayload:
    response = await client.post("/api/v1/session/login", headers=_auth_headers())
    assert response.status_code == 200
    return SessionPayload.model_validate_json(response.content)


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
