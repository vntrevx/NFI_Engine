from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict

from nfi_engine.api.app import create_app
from nfi_engine.api.auth import ApiErrorResponse
from nfi_engine.api.errors import ApiErrorCode
from nfi_engine.api.update_models import UpdatePreviewResponse, UpdateProofReceiptResponse
from nfi_engine.config.models import ApiSettings, EngineSettings, RuntimeSettings, UiSettings

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
async def test_update_preview_returns_local_provenance_contract() -> None:
    # Given: an authorized operator client backed by a local config file.
    client = _client(
        create_app(settings=_settings(), config_path=Path("examples/futures-paper.yaml"))
    )

    # When: the update preview endpoint is called through the protected read surface.
    response = await client.get("/api/v1/update/preview", headers=_auth_headers())
    payload = UpdatePreviewResponse.model_validate_json(response.content)

    # Then: the preview exposes a local-only provenance summary.
    assert response.status_code == 200
    assert payload.provenance_verified is True
    assert payload.remote_network_allowed is False
    assert payload.live_blocked is False
    assert payload.workspace_state in {"clean", "dirty", "unavailable"}
    assert isinstance(payload.workspace_dirty, bool)
    assert payload.strategy_name == "AdapterSmokeStrategy"
    assert payload.rollback_state.status == "backup_required"


@pytest.mark.anyio
async def test_update_preview_uses_env_config_path_for_uvicorn_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given: the same config path style used by `nfi-engine serve`.
    config_path = Path("examples/futures-paper.yaml")
    monkeypatch.setenv("NFI_ENGINE_CONFIG", str(config_path))
    client = _client(create_app())

    # When: the uvicorn-factory app builds a local update preview.
    response = await client.get("/api/v1/update/preview")
    payload = UpdatePreviewResponse.model_validate_json(response.content)

    # Then: provenance uses the real config file instead of runtime-only fallback.
    assert response.status_code == 200
    assert payload.config_source == str(config_path)
    assert payload.provenance_verified is True
    assert payload.live_blocked is False


@pytest.mark.anyio
async def test_update_apply_returns_blocked_receipt_without_backup_reference() -> None:
    # Given: an authorized operator client using runtime-only provenance.
    client = _client(create_app(settings=_settings()))
    session = await _login(client)

    # When: apply proof is requested without backup evidence.
    response = await client.post("/api/v1/update/apply", headers=_csrf_headers(session), json={})
    payload = UpdateProofReceiptResponse.model_validate_json(response.content)

    # Then: the route returns a typed blocked receipt instead of mutating state.
    assert response.status_code == 200
    assert payload.action == "apply"
    assert payload.accepted is False
    assert payload.source_mutated is False
    assert payload.remote_network_allowed is False
    assert payload.restart_required is False
    assert payload.reload_required is False
    assert "backup_reference_required" in payload.blocked_reasons
    assert "acknowledge_unverified_required" in payload.blocked_reasons


@pytest.mark.anyio
async def test_update_rollback_returns_blocked_receipt_without_backup_reference() -> None:
    # Given: an authorized operator client with runtime-only provenance.
    client = _client(create_app(settings=_settings()))
    session = await _login(client)
    before = await client.get("/api/v1/config/current", headers=_auth_headers())

    # When: rollback proof is requested without backup evidence.
    response = await client.post("/api/v1/update/rollback", headers=_csrf_headers(session), json={})
    after = await client.get("/api/v1/config/current", headers=_auth_headers())
    payload = UpdateProofReceiptResponse.model_validate_json(response.content)

    # Then: rollback is blocked without mutating runtime config.
    assert response.status_code == 200
    assert payload.action == "rollback"
    assert payload.accepted is False
    assert payload.mutation_applied is False
    assert payload.source_mutated is False
    assert "backup_reference_required" in payload.blocked_reasons
    assert before.content == after.content


@pytest.mark.anyio
async def test_update_rollback_requires_csrf_on_write_route() -> None:
    # Given: a logged-in operator without a CSRF header.
    client = _client(create_app(settings=_settings()))
    await _login(client)

    # When: rollback proof is posted without the CSRF token.
    response = await client.post(
        "/api/v1/update/rollback",
        json={"backup_reference": "backups/local-proof.zip", "acknowledge_unverified": True},
    )
    payload = ErrorEnvelope.model_validate_json(response.content)

    # Then: the write route is rejected by the shared CSRF guard.
    assert response.status_code == 403
    assert payload.detail.code is ApiErrorCode.CSRF_TOKEN_REQUIRED


@pytest.mark.anyio
async def test_update_apply_rejects_malformed_payload_with_422() -> None:
    # Given: an authorized operator client.
    client = _client(create_app(settings=_settings()))
    session = await _login(client)

    # When: apply proof is called with a non-string backup reference.
    response = await client.post(
        "/api/v1/update/apply",
        headers=_csrf_headers(session),
        json={"backup_reference": 7, "acknowledge_unverified": "yes"},
    )

    # Then: malformed input is rejected by strict request parsing.
    assert response.status_code == 422


@pytest.mark.anyio
async def test_update_apply_blocks_invalid_update_source_even_with_safe_overrides() -> None:
    # Given: an authorized operator client with explicit backup and dirty-worktree policy.
    client = _client(create_app(settings=_settings()))
    session = await _login(client)

    # When: apply proof claims a source outside the local proof channel.
    response = await client.post(
        "/api/v1/update/apply",
        headers=_csrf_headers(session),
        json={
            "backup_reference": "backups/local-proof.zip",
            "acknowledge_unverified": True,
            "allow_dirty_worktree": True,
            "update_source": "remote_plugin",
        },
    )
    payload = UpdateProofReceiptResponse.model_validate_json(response.content)

    # Then: the route blocks the source policy without mutating runtime state.
    assert response.status_code == 200
    assert payload.accepted is False
    assert payload.source_mutated is False
    assert payload.update_source == "remote_plugin"
    assert "invalid_update_source" in payload.blocked_reasons


@pytest.mark.anyio
async def test_update_preview_remains_readable_while_read_only_blocks_apply() -> None:
    # Given: a read-only local console session.
    client = _client(create_app(settings=_settings(read_only=True)))
    session = await _login(client)

    # When: preview and apply are both requested.
    preview = await client.get("/api/v1/update/preview", headers=_auth_headers())
    apply = await client.post(
        "/api/v1/update/apply",
        headers=_csrf_headers(session),
        json={"backup_reference": "backups/local-proof.zip", "acknowledge_unverified": True},
    )
    error = ErrorEnvelope.model_validate_json(apply.content)

    # Then: inspection still works, but mutation-like proof actions use the write gate.
    assert preview.status_code == 200
    assert apply.status_code == 403
    assert error.detail.code is ApiErrorCode.READONLY_ACTION_BLOCKED


def _settings(
    *,
    bearer: str = LOCAL_BEARER,
    environment: str = "local",
    read_only: bool = False,
) -> RuntimeSettings:
    return RuntimeSettings(
        engine=EngineSettings(environment=environment),
        api=ApiSettings.model_validate({"auth_token": bearer}),
        ui=UiSettings(read_only=read_only),
    )


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
