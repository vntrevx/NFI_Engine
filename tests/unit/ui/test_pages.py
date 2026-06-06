from __future__ import annotations

from nfi_engine.api.models import initial_log_entries
from nfi_engine.config.models import RuntimeSettings, UiSettings
from nfi_engine.ui.pages import render_logs_page, render_settings_page


def test_settings_page_renders_schema_driven_safe_controls() -> None:
    # Given: default local runtime settings.
    settings = RuntimeSettings()

    # When: the settings page is rendered from frontend metadata.
    html = render_settings_page(settings=settings)

    # Then: safe controls are visible and dangerous/raw surfaces are locked out.
    assert 'data-testid="settings-root"' in html
    assert 'data-testid="settings-form"' in html
    assert 'name="risk.stake_usdt"' in html
    assert 'name="risk.max_open_trades"' in html
    assert 'type="number"' in html
    assert 'data-runtime-safe="true"' in html
    assert 'data-testid="validation-state"' in html
    assert 'data-testid="audit-log"' in html
    assert 'data-testid="live-trading-locked"' in html
    assert "raw yaml" not in html.lower()
    assert "exchange.api_secret" not in html
    assert "api.auth_token" not in html
    assert "https://" not in html
    assert "cdn" not in html.lower()


def test_logs_page_renders_error_filter_and_report_controls() -> None:
    # Given: seeded operator logs.
    logs = initial_log_entries()

    # When: the logs page is rendered.
    html = render_logs_page(logs=logs)

    # Then: the operator can filter errors and export a redacted support report.
    assert 'data-testid="logs-root"' in html
    assert 'data-testid="severity-filter"' in html
    assert 'data-testid="error-search"' in html
    assert 'data-testid="error-detail"' in html
    assert 'data-testid="correlation-id"' in html
    assert 'data-testid="export-support-report"' in html
    assert "/api/v1/reports/support-bundle.zip" in html
    assert "CONFIG_VALIDATION_ERROR" in html
    assert "traceback" not in html.lower()
    assert "https://" not in html


def test_read_only_settings_page_locks_mutating_controls_without_token_storage() -> None:
    # Given: read-only operator settings.
    settings = RuntimeSettings(ui=UiSettings(read_only=True))

    # When: the settings page is rendered.
    html = render_settings_page(settings=settings)

    # Then: mutation controls are disabled with a visible reason and no token storage.
    assert 'data-testid="readonly-reason"' in html
    assert 'data-testid="save-draft-button" disabled' in html
    assert 'data-testid="apply-button" disabled' in html
    assert 'data-testid="restore-button" disabled' in html
    assert 'data-testid="start-button" disabled' in html
    assert 'data-testid="stop-button" disabled' in html
    assert "Read-only mode blocks changes" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
