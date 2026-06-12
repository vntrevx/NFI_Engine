from __future__ import annotations

from io import BytesIO
from typing import TYPE_CHECKING, Final
from zipfile import ZipFile

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.api.models import (
    ConfigApplyResponse,
    ConfigCurrentResponse,
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
        invalid_locale = await client.post(
            "/api/v1/config/validate",
            json={"fields": [{"path": "ui.locale", "value": "jp"}]},
        )
        valid_locale = await client.post(
            "/api/v1/config/validate",
            json={"fields": [{"path": "ui.locale", "value": "ko"}]},
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
    assert 'data-testid="simple-settings"' in page.text
    assert 'data-testid="setup-preview-panel"' in page.text
    assert 'data-testid="setup-preview-button"' in page.text
    assert 'name="intent"' in page.text
    assert 'name="risk_preset"' in page.text
    assert 'name="api_key" type="password"' in page.text
    assert 'name="api_secret" type="password"' in page.text
    assert 'data-testid="advanced-settings"' in page.text
    assert 'name="ui.locale"' in page.text
    assert 'name="risk.max_open_trades"' in page.text
    assert 'data-testid="field-exchange.trading_mode" data-runtime-safe="false" disabled' in (
        page.text
    )
    assert "/api/v1/config/current" in page.text
    assert "https://" not in page.text
    assert "cdn" not in page.text.lower()
    assert "raw yaml" not in page.text.lower()

    invalid_payload = ConfigValidationResponse.model_validate_json(invalid.content)
    valid_payload = ConfigValidationResponse.model_validate_json(valid.content)
    invalid_locale_payload = ConfigValidationResponse.model_validate_json(invalid_locale.content)
    valid_locale_payload = ConfigValidationResponse.model_validate_json(valid_locale.content)
    draft_payload = ConfigDraftResponse.model_validate_json(draft.content)
    applied_payload = ConfigApplyResponse.model_validate_json(applied.content)
    unsafe_payload = ConfigValidationResponse.model_validate_json(unsafe.content)
    assert invalid_payload.valid is False
    assert "risk.max_open_trades must be at least 1" in invalid_payload.errors
    assert valid_payload.valid is True
    assert invalid_locale_payload.valid is False
    assert "ui.locale must be en, ko, or el" in invalid_locale_payload.errors
    assert valid_locale_payload.valid is True
    assert draft_payload.accepted is True
    assert applied_payload.applied is True
    assert applied_payload.restart_required is False
    assert applied_payload.errors == ()
    assert applied_payload.next_action is None
    assert unsafe_payload.valid is False
    assert "engine.live_trading is locked for milestone 1" in unsafe_payload.errors


@pytest.mark.anyio
async def test_config_apply_mutates_safe_fields_and_blocks_restart_fields() -> None:
    # Given: a local console with a CSRF token from the settings page.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        page = await client.get("/settings")
        csrf_headers = _csrf_headers_from_page(page.text)

        # When: a safe risk field, a restart-required field, and an invalid field are applied.
        applied = await client.post(
            "/api/v1/config/apply",
            headers=csrf_headers,
            json={"fields": [{"path": "risk.max_open_trades", "value": "4"}]},
        )
        current_after_apply = await client.get("/api/v1/config/current")
        restart_required = await client.post(
            "/api/v1/config/apply",
            headers=csrf_headers,
            json={"fields": [{"path": "exchange.name", "value": "binance"}]},
        )
        current_after_restart_required = await client.get("/api/v1/config/current")
        invalid_apply = await client.post(
            "/api/v1/config/apply",
            headers=csrf_headers,
            json={"fields": [{"path": "risk.max_open_trades", "value": "0"}]},
        )

    # Then: safe fields mutate runtime settings and restart-required fields stay pending.
    applied_payload = ConfigApplyResponse.model_validate_json(applied.content)
    current_payload = ConfigCurrentResponse.model_validate_json(current_after_apply.content)
    restart_payload = ConfigApplyResponse.model_validate_json(restart_required.content)
    restart_current_payload = ConfigCurrentResponse.model_validate_json(
        current_after_restart_required.content,
    )
    invalid_apply_payload = ConfigApplyResponse.model_validate_json(invalid_apply.content)
    assert applied_payload.applied is True
    assert applied_payload.restart_required is False
    assert current_payload.risk.max_open_trades == 4
    assert restart_payload.applied is False
    assert restart_payload.restart_required is True
    assert restart_payload.errors == ("exchange.name requires restart before it can apply",)
    assert restart_payload.next_action == "Save the draft, then restart NFI Engine."
    assert restart_current_payload.exchange.name == "simulator"
    assert invalid_apply_payload.applied is False
    assert invalid_apply_payload.errors == ("risk.max_open_trades must be at least 1",)
    assert invalid_apply_payload.next_action == "Fix the invalid setting values and retry."


@pytest.mark.anyio
async def test_config_apply_updates_runtime_ui_and_write_gate_surfaces() -> None:
    # Given: a local console with an English, writable runtime.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        page = await client.get("/settings")
        csrf_headers = _csrf_headers_from_page(page.text)

        # When: runtime-safe UI settings are applied.
        locale_apply = await client.post(
            "/api/v1/config/apply",
            headers=csrf_headers,
            json={"fields": [{"path": "ui.locale", "value": "ko"}]},
        )
        localized_page = await client.get("/settings")
        read_only_apply = await client.post(
            "/api/v1/config/apply",
            headers=csrf_headers,
            json={"fields": [{"path": "ui.read_only", "value": "true"}]},
        )
        blocked_write = await client.post(
            "/api/v1/config/apply",
            headers=csrf_headers,
            json={"fields": [{"path": "risk.max_open_trades", "value": "4"}]},
        )

    # Then: UI rendering and server write gates both read the current runtime settings.
    locale_payload = ConfigApplyResponse.model_validate_json(locale_apply.content)
    read_only_payload = ConfigApplyResponse.model_validate_json(read_only_apply.content)
    assert locale_payload.applied is True
    assert read_only_payload.applied is True
    assert localized_page.status_code == 200
    assert '<html lang="ko">' in localized_page.text
    assert "로컬 운영자 설정" in localized_page.text
    assert blocked_write.status_code == 403
    assert b'"code":"READONLY_ACTION_BLOCKED"' in blocked_write.content
    assert b'"message":"read-only mode blocks changes"' in blocked_write.content


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
