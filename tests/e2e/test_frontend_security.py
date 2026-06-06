from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, ClassVar, Final

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict

from nfi_engine.api.app import create_app
from nfi_engine.config.models import ApiSettings, RuntimeSettings, UiSettings

if TYPE_CHECKING:
    from fastapi import FastAPI

LOCAL_BEARER: Final = "local-test-bearer"


class ErrorDetail(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    code: str
    message: str
    audit_event: str | None = None


class ErrorEnvelope(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    detail: ErrorDetail


class SessionPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    role: str
    csrf_token: str
    expires_at: datetime


class AuditEventPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    code: str
    route: str
    role: str


class AuditLogPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    items: tuple[AuditEventPayload, ...]


@pytest.mark.anyio
async def test_session_login_logout_and_expiry_when_operator_uses_console() -> None:
    # Given: a token-protected local console.
    async with _client(create_app(settings=_settings())) as client:
        # When: the operator logs in with the bearer token.
        unauthenticated_settings = await client.get("/settings")
        unauthenticated_audit = await client.get("/api/v1/security/audit")
        login = await client.post("/api/v1/session/login", headers=_auth_headers())
        session = SessionPayload.model_validate_json(login.content)
        settings_page = await client.get("/settings")
        current = await client.get("/api/v1/session/current")
        logout = await client.post(
            "/api/v1/session/logout",
            headers=_csrf_headers(session),
        )
        after_logout = await client.get("/api/v1/session/current")

    # Then: a session cookie and CSRF token are issued, then invalidated on logout.
    assert unauthenticated_settings.status_code == 401
    assert unauthenticated_audit.status_code == 401
    assert login.status_code == 200
    assert "nfi_engine_session" in login.headers["set-cookie"]
    assert "nfi_engine_csrf" in login.headers["set-cookie"]
    assert session.role == "operator"
    assert session.csrf_token != ""
    assert _csrf_token_from_page(settings_page.text) == session.csrf_token
    assert current.status_code == 200
    assert logout.status_code == 200
    assert after_logout.status_code == 401

    # Given: a session configured to expire immediately.
    expired_settings = _settings(session_ttl_seconds=0)
    async with _client(create_app(settings=expired_settings)) as client:
        # When: the operator logs in and immediately uses the session.
        expired_login = await client.post("/api/v1/session/login", headers=_auth_headers())
        expired_session = SessionPayload.model_validate_json(expired_login.content)
        expired_current = await client.get(
            "/api/v1/session/current",
            headers=_csrf_headers(expired_session),
        )
        expired_error = ErrorEnvelope.model_validate_json(expired_current.content)

    # Then: expired sessions are rejected with a typed error.
    assert expired_login.status_code == 200
    assert expired_current.status_code == 401
    assert expired_error.detail.code == "SESSION_EXPIRED"


@pytest.mark.anyio
async def test_csrf_blocks_mutating_settings_request_when_header_is_missing() -> None:
    # Given: a token-protected local API.
    async with _client(create_app(settings=_settings())) as client:
        # When: a mutating settings request is sent with bearer auth but no CSRF token.
        response = await client.post(
            "/api/v1/config/apply",
            headers=_auth_headers(),
        )
        await _login(client)
        invalid = await client.post(
            "/api/v1/config/apply",
            headers={"x-nfi-csrf-token": "wrong-token"},
            json={"fields": [{"path": "risk.max_open_trades", "value": "4"}]},
        )
        error = ErrorEnvelope.model_validate_json(response.content)
        invalid_error = ErrorEnvelope.model_validate_json(invalid.content)

    # Then: the request is rejected before body validation or mutation.
    assert response.status_code == 403
    assert error.detail.code == "CSRF_TOKEN_REQUIRED"
    assert invalid.status_code == 403
    assert invalid_error.detail.code == "CSRF_TOKEN_INVALID"


@pytest.mark.anyio
async def test_read_only_mode_blocks_mutations_but_keeps_inspection_available() -> None:
    # Given: a read-only local console session.
    settings = _settings(read_only=True)
    async with _client(create_app(settings=settings)) as client:
        session = await _login(client)
        headers = _csrf_headers(session)

        # When: read-only inspection surfaces are opened.
        settings_page = await client.get("/settings")
        logs_page = await client.get("/logs")
        pairlist_preview = await client.post(
            "/api/v1/pairlist/preview",
            headers=headers,
            json={"blacklist": "DOGE/USDT:USDT"},
        )

        # When: read-only mode attempts mutating actions.
        config_apply = await client.post(
            "/api/v1/config/apply",
            headers=headers,
            json={"fields": [{"path": "risk.max_open_trades", "value": "4"}]},
        )
        pairlist_apply = await client.post(
            "/api/v1/pairlist/apply",
            headers=headers,
            json={"blacklist": "DOGE/USDT:USDT"},
        )
        backup_restore = await client.post("/api/v1/backup/restore", headers=headers, json={})
        runtime_start = await client.post("/api/v1/start", headers=headers)
        audit = await client.get("/api/v1/security/audit")

    # Then: reads work, writes fail server-side, and security audit events are visible.
    assert settings_page.status_code == 200
    assert logs_page.status_code == 200
    assert pairlist_preview.status_code == 200
    for response in (config_apply, pairlist_apply, backup_restore, runtime_start):
        error = ErrorEnvelope.model_validate_json(response.content)
        assert response.status_code == 403
        assert error.detail.code == "READONLY_ACTION_BLOCKED"
        assert error.detail.audit_event == "READONLY_ACTION_BLOCKED"
    audit_payload = AuditLogPayload.model_validate_json(audit.content)
    assert "READONLY_ACTION_BLOCKED" in {item.code for item in audit_payload.items}


def _settings(
    *,
    read_only: bool = False,
    session_ttl_seconds: int = 1800,
) -> RuntimeSettings:
    return RuntimeSettings(
        api=ApiSettings.model_validate(
            {"auth_token": LOCAL_BEARER, "session_ttl_seconds": session_ttl_seconds},
        ),
        ui=UiSettings(read_only=read_only),
    )


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {LOCAL_BEARER}"}


def _csrf_headers(session: SessionPayload) -> dict[str, str]:
    return {"x-nfi-csrf-token": session.csrf_token}


def _csrf_token_from_page(html: str) -> str:
    marker = '<meta name="nfi-csrf-token" content="'
    return html.split(marker, maxsplit=1)[1].split('"', maxsplit=1)[0]


async def _login(client: AsyncClient) -> SessionPayload:
    response = await client.post("/api/v1/session/login", headers=_auth_headers())
    assert response.status_code == 200
    return SessionPayload.model_validate_json(response.content)


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
