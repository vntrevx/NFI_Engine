from __future__ import annotations

from datetime import UTC, datetime
from io import BytesIO
from zipfile import ZipFile

from nfi_engine.api.models import LogEntryResponse, support_bundle_response
from nfi_engine.api.support_bundle import support_bundle_zip
from nfi_engine.config.enums import LogLevel
from nfi_engine.config.models import ApiSettings, ExchangeSettings, RuntimeSettings
from nfi_engine.events import REDACTED_TEXT


def test_support_bundle_zip_redacts_secret_values_embedded_in_logs() -> None:
    # Given: runtime settings and a log entry that accidentally carries secret values.
    settings = RuntimeSettings(
        exchange=ExchangeSettings.model_validate(
            {"api_key": "fixture-api-key", "api_secret": "fixture-api-secret"},
        ),
        api=ApiSettings.model_validate({"auth_token": "fixture-api-token"}),
    )
    logs = (
        LogEntryResponse(
            at=datetime.now(UTC),
            level=LogLevel.ERROR,
            code="SUPPORT_BUNDLE_REDACTION_PROBE",
            message="fixture-api-secret appeared in a diagnostic message",
            correlation_id="fixture-correlation",
            command="nfi-engine --token fixture-api-token",
            route="/api/v1/probe/fixture-api-key",
            safe_summary="fixture-api-key and fixture-api-secret in summary",
            report_hint="fixture-api-token in hint",
        ),
    )

    # When: a support bundle is generated from the settings and logs.
    payload = support_bundle_zip(support_bundle_response(settings=settings, logs=logs))

    # Then: every bundle member is serialized without the original secret values.
    with ZipFile(BytesIO(payload)) as archive:
        merged = "\n".join(archive.read(name).decode("utf-8") for name in archive.namelist())
    assert REDACTED_TEXT in merged
    assert "fixture-api-key" not in merged
    assert "fixture-api-secret" not in merged
    assert "fixture-api-token" not in merged
