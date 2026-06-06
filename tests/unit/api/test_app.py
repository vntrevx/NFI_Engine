from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, ClassVar

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict

from nfi_engine.api.app import create_app
from nfi_engine.api.auth import ApiErrorResponse
from nfi_engine.api.errors import ApiConfigurationError, ApiErrorCode
from nfi_engine.api.models import (
    REDACTED,
    ConfigSchemaResponse,
    ErrorLookupResponse,
    LogListResponse,
    PingResponse,
    StateResponse,
    SupportBundleResponse,
)
from nfi_engine.api.settings import validate_api_auth_settings
from nfi_engine.config.models import ApiSettings, EngineSettings, RuntimeSettings

if TYPE_CHECKING:
    from fastapi import FastAPI
    from starlette.types import Message, Scope

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
async def test_ping_is_public_when_no_token_is_sent() -> None:
    # Given: an API app with a configured operator token.
    client = _client(create_app(settings=_settings()))

    # When: the public ping endpoint is called without credentials.
    response = await client.get("/api/v1/ping")
    payload = PingResponse.model_validate_json(response.content)

    # Then: the endpoint returns the public health signal.
    assert response.status_code == 200
    assert payload.status == "pong"


@pytest.mark.anyio
async def test_status_requires_bearer_token_when_missing() -> None:
    # Given: an API app with protected operator endpoints.
    client = _client(create_app(settings=_settings()))

    # When: status is requested without a bearer token.
    response = await client.get("/api/v1/status")
    payload = ErrorEnvelope.model_validate_json(response.content)

    # Then: the request is rejected before state is exposed.
    assert response.status_code == 401
    assert payload.detail.code is ApiErrorCode.API_AUTH_REQUIRED


@pytest.mark.anyio
async def test_control_endpoints_apply_state_transitions_when_authorized() -> None:
    # Given: an authorized local operator client.
    client = _client(create_app(settings=_settings()))
    session = await _login(client)
    headers = _csrf_headers(session)

    # When: start, pause, and stop commands are issued.
    started = await client.post("/api/v1/start", headers=headers)
    paused = await client.post("/api/v1/pause", headers=headers)
    stopped = await client.post("/api/v1/stop", headers=headers)

    # Then: each command returns the observable bot state.
    assert StateResponse.model_validate_json(started.content).state == "running"
    assert StateResponse.model_validate_json(paused.content).state == "paused"
    assert StateResponse.model_validate_json(stopped.content).state == "stopped"


@pytest.mark.anyio
async def test_config_logs_errors_and_report_endpoints_return_frontend_contracts() -> None:
    # Given: an authorized frontend client.
    client = _client(create_app(settings=_settings()))
    headers = _auth_headers()

    # When: frontend support endpoints are read.
    schema = await client.get("/api/v1/config/schema", headers=headers)
    logs = await client.get("/api/v1/logs/recent?limit=20", headers=headers)
    error = await client.get("/api/v1/errors/TICK_PARSE_ERROR", headers=headers)
    report = await client.get("/api/v1/reports/support-bundle", headers=headers)
    schema_payload = ConfigSchemaResponse.model_validate_json(schema.content)
    logs_payload = LogListResponse.model_validate_json(logs.content)
    error_payload = ErrorLookupResponse.model_validate_json(error.content)
    report_payload = SupportBundleResponse.model_validate_json(report.content)

    # Then: the responses expose typed, redacted operator data.
    assert schema.status_code == 200
    assert schema_payload.fields[0].path == "engine.live_trading"
    assert logs.status_code == 200
    assert isinstance(logs_payload.items, tuple)
    assert error.status_code == 200
    assert error_payload.code == "TICK_PARSE_ERROR"
    assert report.status_code == 200
    assert report_payload.redacted_config.exchange.api_secret == REDACTED


@pytest.mark.anyio
async def test_websocket_route_rejects_missing_token() -> None:
    # Given: the protected WebSocket route as an ASGI app.
    app = create_app(settings=_settings())

    # When: a connection is attempted without a token.
    sent_messages = await _websocket_messages(app, _websocket_scope())

    # Then: the route closes the connection with policy violation.
    assert sent_messages[0]["type"] == "websocket.close"
    assert sent_messages[0]["code"] == 1008


@pytest.mark.anyio
async def test_websocket_route_rejects_query_token_without_session_cookie() -> None:
    # Given: the protected WebSocket route as an ASGI app.
    app = create_app(settings=_settings())

    # When: a bearer-equivalent token is sent through the URL query string.
    sent_messages = await _websocket_messages(
        app,
        _websocket_scope(query_string=b"token=local-test-bearer"),
    )

    # Then: the route rejects the URL token instead of accepting leaked credentials.
    assert sent_messages[0]["type"] == "websocket.close"
    assert sent_messages[0]["code"] == 1008


@pytest.mark.anyio
async def test_websocket_route_accepts_session_cookie() -> None:
    # Given: a logged-in operator with a server-issued session cookie.
    app = create_app(settings=_settings())
    client = _client(app)
    await _login(client)
    session_id = client.cookies.get("nfi_engine_session")
    assert session_id is not None

    # When: the WebSocket handshake includes the session cookie.
    sent_messages = await _websocket_messages(
        app,
        _websocket_scope(headers=((b"cookie", f"nfi_engine_session={session_id}".encode()),)),
    )

    # Then: the connection opens without using a URL token.
    assert sent_messages[0]["type"] == "websocket.accept"
    assert sent_messages[1]["type"] == "websocket.send"
    assert sent_messages[2]["type"] == "websocket.close"


def test_auth_validation_rejects_weak_token_outside_local_environment() -> None:
    # Given: a production environment with an operator token that is only for local QA.
    settings = _settings(bearer="test-token", environment="production")

    # When/Then: startup auth validation rejects the weak secret.
    with pytest.raises(ApiConfigurationError, match=ApiErrorCode.API_WEAK_AUTH_VALUE):
        validate_api_auth_settings(settings)


def _settings(*, bearer: str = LOCAL_BEARER, environment: str = "local") -> RuntimeSettings:
    return RuntimeSettings(
        engine=EngineSettings(environment=environment),
        api=ApiSettings.model_validate({"auth_token": bearer}),
    )


def _auth_headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {LOCAL_BEARER}"}


def _csrf_headers(session: SessionPayload) -> dict[str, str]:
    return {"x-nfi-csrf-token": session.csrf_token}


async def _login(client: AsyncClient) -> SessionPayload:
    response = await client.post("/api/v1/session/login", headers=_auth_headers())
    assert response.status_code == 200
    return SessionPayload.model_validate_json(response.content)


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


async def _websocket_messages(app: FastAPI, scope: Scope) -> list[Message]:
    sent_messages: list[Message] = []
    first_receive = True

    async def receive() -> Message:
        nonlocal first_receive
        if first_receive:
            first_receive = False
            return {"type": "websocket.connect"}
        return {"type": "websocket.disconnect", "code": 1000}

    async def send(message: Message) -> None:
        sent_messages.append(message)

    await app(scope, receive, send)
    return sent_messages


def _websocket_scope(
    *,
    headers: tuple[tuple[bytes, bytes], ...] = (),
    query_string: bytes = b"",
) -> Scope:
    return {
        "type": "websocket",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "scheme": "ws",
        "path": "/api/v1/message/ws",
        "raw_path": b"/api/v1/message/ws",
        "query_string": query_string,
        "root_path": "",
        "headers": list(headers),
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
        "subprotocols": [],
    }
