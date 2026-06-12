from __future__ import annotations

from nfi_engine.api.models import initial_log_entries
from nfi_engine.config import Locale
from nfi_engine.config.models import RuntimeSettings, UiSettings
from nfi_engine.ui.pages import render_home_page, render_logs_page, render_settings_page


def test_settings_page_renders_schema_driven_safe_controls() -> None:
    # Given: default local runtime settings.
    settings = RuntimeSettings()

    # When: the settings page is rendered from frontend metadata.
    html = render_settings_page(settings=settings)

    # Then: safe controls are visible and dangerous/raw surfaces are locked out.
    assert 'data-testid="settings-root"' in html
    assert 'data-testid="settings-form"' in html
    assert 'data-testid="setup-form"' in html
    assert 'name="intent"' in html
    assert 'name="risk_preset"' in html
    assert 'name="api_key" type="password"' in html
    assert 'name="api_secret" type="password"' in html
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
    assert 'value="real-secret"' not in html
    assert "https://" not in html
    assert "cdn" not in html.lower()


def test_home_page_renders_operator_command_center_without_external_assets() -> None:
    settings = RuntimeSettings()
    html = render_home_page(settings=settings, logs=initial_log_entries())

    assert 'data-testid="home-root"' in html
    assert 'data-testid="home-nav"' in html
    assert 'data-testid="setup-doctor"' in html
    assert 'data-testid="safety-explainer"' in html
    assert 'data-testid="support-shortcut"' in html
    assert 'data-testid="home-chart-shell"' in html
    assert 'data-testid="dashboard-chart"' in html
    assert 'data-testid="chart-status"' in html
    assert 'data-testid="chart-render-time"' in html
    assert 'data-poll-ms="5000"' in html
    assert 'data-testid="pairlist-summary"' in html
    assert 'data-testid="recent-errors"' in html
    assert "/api/v1/dashboard/snapshot" in html
    assert "Operator command center" in html
    assert "chart-bars" not in html
    assert "landing" not in html.lower()
    assert "https://" not in html
    assert "cdn" not in html.lower()
    assert "localStorage" not in html
    assert "sessionStorage" not in html


def test_settings_page_keeps_advanced_fields_discoverable_without_sensitive_values() -> None:
    # Given: default local runtime settings before Simple Mode is expanded.
    settings = RuntimeSettings()

    # When: the settings page is rendered.
    html = render_settings_page(settings=settings)

    # Then: advanced runtime-safe controls remain in the page while secrets stay hidden.
    assert 'name="notifications.max_attempts"' in html
    assert 'name="backtest.fee_rate"' in html
    assert "exchange.api_key" not in html
    assert "exchange.api_secret" not in html


def test_settings_page_renders_simple_mode_before_advanced_controls() -> None:
    # Given: default local runtime settings.
    settings = RuntimeSettings()

    # When: the settings page is rendered.
    html = render_settings_page(settings=settings)

    # Then: essential setup fields are grouped before advanced controls.
    simple_start = html.index('data-testid="simple-settings"')
    setup_start = html.index('data-testid="setup-preview-panel"')
    advanced_start = html.index('data-testid="advanced-settings"')
    setup_html = html[setup_start:simple_start]
    simple_html = html[simple_start:advanced_start]
    assert setup_start < simple_start
    assert simple_start < advanced_start
    assert 'name="intent"' in setup_html
    assert 'name="risk_preset"' in setup_html
    assert 'name="api_key" type="password"' in setup_html
    assert 'name="api_secret" type="password"' in setup_html
    assert 'name="exchange.name"' in simple_html
    assert 'name="exchange.trading_mode"' in simple_html
    assert 'name="ui.locale"' in simple_html
    assert 'name="risk.stake_usdt"' in simple_html
    assert 'name="risk.max_open_trades"' in simple_html


def test_logs_page_renders_error_filter_and_report_controls() -> None:
    # Given: seeded operator logs.
    logs = initial_log_entries()
    settings = RuntimeSettings()

    # When: the logs page is rendered.
    html = render_logs_page(settings=settings, logs=logs)

    # Then: the operator can filter errors and export a redacted support report.
    assert 'data-testid="logs-root"' in html
    assert 'data-testid="severity-filter"' in html
    assert 'data-testid="logs-table-scroll"' in html
    assert 'class="logs-table"' in html
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


def test_home_page_uses_configured_locale_in_document_lang() -> None:
    # Given: Korean frontend settings.
    settings = RuntimeSettings(ui=UiSettings(locale=Locale.KO))

    # When: the home page is rendered.
    html = render_home_page(settings=settings, logs=initial_log_entries())

    # Then: document language changes without altering stable test ids.
    assert '<html lang="ko">' in html
    assert 'data-testid="home-root"' in html
