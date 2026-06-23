from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Final

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict

from nfi_engine.api.app import create_app
from nfi_engine.config.models import (
    ApiSettings,
    CircuitBreakerSettings,
    EngineSettings,
    ReconciliationSettings,
    RuntimeSettings,
)
from nfi_engine.dashboard.store import StaticDashboardReadStore

if TYPE_CHECKING:
    from fastapi import FastAPI

LOCAL_BEARER: Final = "local-test-bearer"


class SessionPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    role: str
    csrf_token: str
    expires_at: datetime


class RuntimeControlPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    state: str
    new_entries_allowed: bool


class ErrorDetail(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    code: str
    message: str
    audit_event: str | None = None


class ErrorEnvelope(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    detail: ErrorDetail


pytestmark = pytest.mark.anyio


async def test_runtime_control_routes_share_typed_state_surface() -> None:
    # Given: a local operator session with an empty dashboard store.
    settings = RuntimeSettings(api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}))
    async with _client(
        create_app(settings=settings, dashboard_store=StaticDashboardReadStore()),
    ) as client:
        session = await _login(client)
        headers = _csrf_headers(session)

        # When: runtime is driven through the generic and compatibility control routes.
        start = await client.post(
            "/api/v1/runtime/control",
            headers=headers,
            json={"command": "start"},
        )
        pause = await client.post("/api/v1/pause", headers=headers)
        resume = await client.post("/api/v1/resume", headers=headers)
        current = await client.get("/api/v1/runtime/control", headers=_auth_headers())

        # Then: each route returns the same typed runtime-control contract.
        start_payload = RuntimeControlPayload.model_validate_json(start.content)
        pause_payload = RuntimeControlPayload.model_validate_json(pause.content)
        resume_payload = RuntimeControlPayload.model_validate_json(resume.content)
        current_payload = RuntimeControlPayload.model_validate_json(current.content)
        assert start.status_code == 200
        assert start_payload.state == "running"
        assert start_payload.new_entries_allowed is True
        assert pause.status_code == 200
        assert pause_payload.state == "paused"
        assert pause_payload.new_entries_allowed is False
        assert resume.status_code == 200
        assert resume_payload.state == "running"
        assert resume_payload.new_entries_allowed is True
        assert current.status_code == 200
        assert current_payload.state == "running"
        assert current_payload.new_entries_allowed is True


async def test_runtime_control_rejects_malformed_command_with_machine_code() -> None:
    # Given: a local operator session.
    settings = RuntimeSettings(api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}))
    async with _client(create_app(settings=settings)) as client:
        session = await _login(client)

        # When: the generic control route receives an unknown command.
        response = await client.post(
            "/api/v1/runtime/control",
            headers=_csrf_headers(session),
            json={"command": "explode"},
        )

    # Then: the denial is typed and stable.
    payload = ErrorEnvelope.model_validate_json(response.content)
    assert response.status_code == 422
    assert payload.detail.code == "RUNTIME_COMMAND_INVALID"


async def test_runtime_control_rejects_repeated_pause_and_stop_with_machine_codes() -> None:
    # Given: a local operator session with a running runtime.
    settings = RuntimeSettings(api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}))
    async with _client(create_app(settings=settings)) as client:
        session = await _login(client)
        headers = _csrf_headers(session)
        await client.post("/api/v1/start", headers=headers)
        await client.post("/api/v1/pause", headers=headers)

        # When: pause is repeated and stop is repeated.
        paused_again = await client.post("/api/v1/pause", headers=headers)
        await client.post("/api/v1/stop", headers=headers)
        stopped_again = await client.post("/api/v1/stop", headers=headers)

    # Then: each no-op denial keeps a stable machine code.
    paused_error = ErrorEnvelope.model_validate_json(paused_again.content)
    stopped_error = ErrorEnvelope.model_validate_json(stopped_again.content)
    assert paused_again.status_code == 409
    assert paused_error.detail.code == "RUNTIME_ALREADY_PAUSED"
    assert stopped_again.status_code == 409
    assert stopped_error.detail.code == "RUNTIME_ALREADY_STOPPED"


async def test_runtime_control_rejects_live_intent_with_machine_code() -> None:
    # Given: a local operator session with live trading intent enabled.
    settings = RuntimeSettings(
        api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}),
        engine=EngineSettings(live_trading=True, live_trading_confirmed=True),
    )
    async with _client(create_app(settings=settings)) as client:
        session = await _login(client)

        # When: the operator tries to start runtime entries.
        response = await client.post("/api/v1/start", headers=_csrf_headers(session))

    # Then: live execution remains blocked by a stable control code.
    payload = ErrorEnvelope.model_validate_json(response.content)
    assert response.status_code == 409
    assert payload.detail.code == "RUNTIME_LIVE_UNSAFE"


async def test_runtime_control_blocks_start_while_manual_halt_file_exists(tmp_path: Path) -> None:
    # Given: a manual halt file is present before an operator starts runtime entries.
    halt_file = tmp_path / "manual-halt"
    halt_file.write_text("halt\n", encoding="utf-8")
    settings = RuntimeSettings(
        api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}),
        circuit_breakers=CircuitBreakerSettings(manual_halt_file=str(halt_file)),
    )
    async with _client(
        create_app(settings=settings, dashboard_store=StaticDashboardReadStore())
    ) as client:
        session = await _login(client)
        headers = _csrf_headers(session)

        blocked = await client.post("/api/v1/start", headers=headers)
        halt_file.unlink()
        started = await client.post("/api/v1/start", headers=headers)

    # Then: start is blocked while the halt file exists and succeeds after removal.
    blocked_payload = ErrorEnvelope.model_validate_json(blocked.content)
    started_payload = RuntimeControlPayload.model_validate_json(started.content)
    assert blocked.status_code == 409
    assert blocked_payload.detail.code == "RUNTIME_HEALTH_BLOCKED"
    assert started.status_code == 200
    assert started_payload.state == "running"


async def test_runtime_control_blocks_start_when_reconciliation_preflight_blocks() -> None:
    # Given: startup reconciliation is required and the exchange fixture mismatches state.
    settings = RuntimeSettings(
        api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}),
        reconciliation=ReconciliationSettings(
            required=True,
            fixture_path="tests/fixtures/exchange/reconcile_mismatch.json",
        ),
    )
    async with _client(
        create_app(settings=settings, dashboard_store=StaticDashboardReadStore())
    ) as client:
        session = await _login(client)

        response = await client.post("/api/v1/start", headers=_csrf_headers(session))

    # Then: the runtime-control API promotes the preflight block into a start denial.
    payload = ErrorEnvelope.model_validate_json(response.content)
    assert response.status_code == 409
    assert payload.detail.code == "RUNTIME_PREFLIGHT_BLOCKED"


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
