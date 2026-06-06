from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Final
from zipfile import ZipFile

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.api.models import (
    ConfigApplyResponse,
    ConfigDraftResponse,
    ConfigValidationResponse,
    ErrorLookupResponse,
    LogListResponse,
)
from nfi_engine.config import LogLevel
from nfi_engine.config.models import ApiSettings, ExchangeSettings, RuntimeSettings

if TYPE_CHECKING:
    from fastapi import FastAPI

LOCAL_BEARER: Final = "local-test-bearer"


@pytest.mark.anyio
async def test_settings_ui_and_config_workflow_when_local_console_edits_safe_field() -> None:
    # Given: a local console app without an operator token.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: the settings surface and config workflow are exercised.
        page = await client.get("/settings")
        csrf_headers = _csrf_headers_from_page(page.text)
        invalid = await client.post(
            "/api/v1/config/validate",
            json={"fields": [{"path": "risk.max_open_trades", "value": "0"}]},
        )
        valid = await client.post(
            "/api/v1/config/validate",
            json={"fields": [{"path": "risk.max_open_trades", "value": "4"}]},
        )
        draft = await client.post(
            "/api/v1/config/draft",
            headers=csrf_headers,
            json={"fields": [{"path": "risk.max_open_trades", "value": "4"}]},
        )
        applied = await client.post(
            "/api/v1/config/apply",
            headers=csrf_headers,
            json={"fields": [{"path": "risk.max_open_trades", "value": "4"}]},
        )
        unsafe = await client.post(
            "/api/v1/config/validate",
            json={"fields": [{"path": "engine.live_trading", "value": "true"}]},
        )

    # Then: the UI is local-only HTML and safe changes can be validated/drafted/applied.
    assert page.status_code == 200
    assert "text/html" in page.headers["content-type"]
    assert 'data-testid="settings-root"' in page.text
    assert 'name="risk.max_open_trades"' in page.text
    assert "https://" not in page.text
    assert "cdn" not in page.text.lower()
    assert "raw yaml" not in page.text.lower()

    invalid_payload = ConfigValidationResponse.model_validate_json(invalid.content)
    valid_payload = ConfigValidationResponse.model_validate_json(valid.content)
    draft_payload = ConfigDraftResponse.model_validate_json(draft.content)
    applied_payload = ConfigApplyResponse.model_validate_json(applied.content)
    unsafe_payload = ConfigValidationResponse.model_validate_json(unsafe.content)
    assert invalid_payload.valid is False
    assert "risk.max_open_trades must be at least 1" in invalid_payload.errors
    assert valid_payload.valid is True
    assert draft_payload.accepted is True
    assert applied_payload.applied is True
    assert applied_payload.restart_required is False
    assert unsafe_payload.valid is False
    assert "engine.live_trading is locked for milestone 1" in unsafe_payload.errors


@pytest.mark.anyio
async def test_logs_ui_filters_error_lookup_and_exports_redacted_bundle() -> None:
    # Given: a token-protected local app with secrets in settings.
    settings = RuntimeSettings(
        exchange=ExchangeSettings.model_validate(
            {"api_key": "real-key", "api_secret": "real-secret"},
        ),
        api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}),
    )
    headers = {"Authorization": f"Bearer {LOCAL_BEARER}"}

    async with _client(create_app(settings=settings)) as client:
        # When: the logs surface and report endpoints are exercised.
        login = await client.post("/api/v1/session/login", headers=headers)
        page = await client.get("/logs")
        logs = await client.get("/api/v1/logs/recent?severity=ERROR", headers=headers)
        error = await client.get(
            "/api/v1/errors/CONFIG_VALIDATION_ERROR",
            headers=headers,
        )
        bundle = await client.get("/api/v1/reports/support-bundle.zip", headers=headers)

    # Then: recent errors, correlation IDs, and redacted support bundles are available.
    assert login.status_code == 200
    assert page.status_code == 200
    assert 'data-testid="logs-root"' in page.text
    assert "CONFIG_VALIDATION_ERROR" in page.text
    assert 'data-testid="correlation-id"' in page.text

    log_payload = LogListResponse.model_validate_json(logs.content)
    assert logs.status_code == 200
    assert {item.level for item in log_payload.items} == {LogLevel.ERROR}
    assert log_payload.items[0].code == "CONFIG_VALIDATION_ERROR"
    assert log_payload.items[0].correlation_id != ""

    error_payload = ErrorLookupResponse.model_validate_json(error.content)
    assert error_payload.message == "config validation failed"
    assert error_payload.safe_summary == "config validation failed"
    assert error_payload.correlation_id == log_payload.items[0].correlation_id

    assert bundle.status_code == 200
    assert bundle.headers["content-type"] == "application/zip"
    with ZipFile(BytesIO(bundle.content)) as archive:
        names = set(archive.namelist())
        manifest = archive.read("manifest.json").decode("utf-8")
        merged = "\n".join(archive.read(name).decode("utf-8") for name in sorted(names))
    assert {"config.json", "logs.json", "manifest.json"} <= names
    assert '"checksums"' in manifest
    assert "REDACTED" in merged
    assert "real-secret" not in merged
    assert "real-key" not in merged
    assert LOCAL_BEARER not in merged


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")


def _csrf_headers_from_page(html: str) -> dict[str, str]:
    marker = '<meta name="nfi-csrf-token" content="'
    token = html.split(marker, maxsplit=1)[1].split('"', maxsplit=1)[0]
    return {"x-nfi-csrf-token": token}
