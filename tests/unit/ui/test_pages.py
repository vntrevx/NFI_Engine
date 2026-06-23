from __future__ import annotations

from nfi_engine.api.models import initial_log_entries
from nfi_engine.config import Locale
from nfi_engine.config.models import RuntimeSettings, UiSettings
from nfi_engine.paper import BotState
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.ui.home_context import HomeRuntimeContext
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
    assert 'name="risk_profile"' in html
    assert 'name="permission_withdrawal"' in html
    assert 'name="api_key" type="password"' in html
    assert 'name="api_secret" type="password"' in html
    assert 'name="risk.stake_usdt"' in html
    assert 'name="risk.max_open_trades"' in html
    assert 'type="number"' in html
    assert 'data-runtime-safe="true"' in html
    assert 'data-testid="validation-state"' in html
    assert 'data-testid="audit-log"' in html
    assert 'data-testid="live-trading-locked"' in html
    assert 'data-testid="runtime-control-state"' in html
    assert 'data-testid="runtime-health-state"' in html
    assert 'data-testid="pause-button"' in html
    assert 'data-testid="resume-button"' in html
    assert 'data-command="start"' in html
    assert 'data-command="pause"' in html
    assert 'data-command="resume"' in html
    assert 'data-command="stop"' in html
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
    assert 'data-testid="operator-cockpit"' in html
    assert 'data-testid="cockpit-capability-level"' in html
    assert 'data-testid="cockpit-active-mode"' in html
    assert 'data-testid="cockpit-runtime-health"' in html
    assert 'data-testid="cockpit-wallet-balance"' in html
    assert 'data-testid="cockpit-allocated-amount"' in html
    assert 'data-testid="cockpit-leverage"' in html
    assert 'data-testid="cockpit-risk-profile"' in html
    assert 'data-testid="cockpit-permission-audit"' in html
    assert 'data-testid="cockpit-latest-error"' in html
    assert 'data-testid="cockpit-next-action"' in html
    assert 'data-testid="cockpit-where-next"' in html
    assert 'data-testid="pairlist-summary"' in html
    assert 'data-testid="recent-errors"' in html
    assert 'data-testid="action-queue"' in html
    assert 'data-testid="action-item"' in html
    assert 'data-testid="runtime-controls"' in html
    assert 'data-testid="runtime-control-state"' in html
    assert 'data-testid="pause-button"' in html
    assert 'data-testid="resume-button"' in html
    assert 'data-command="start"' in html
    assert 'data-command="pause"' in html
    assert 'data-command="resume"' in html
    assert 'data-command="stop"' in html
    assert "/api/v1/dashboard/snapshot" in html
    assert "Runtime health" in html
    assert "Operator command center" in html
    assert "chart-bars" not in html
    assert "landing" not in html.lower()
    assert "https://" not in html
    assert "cdn" not in html.lower()
    assert "localStorage" not in html
    assert "sessionStorage" not in html


def test_home_page_uses_runtime_context_bot_state_for_metric_and_control_state() -> None:
    settings = RuntimeSettings()
    html = render_home_page(
        settings=settings,
        logs=(),
        runtime=HomeRuntimeContext(bot_state=BotState.RUNNING),
    )

    assert 'data-testid="bot-state"><span>Bot state</span><strong>running</strong>' in html
    assert 'data-testid="runtime-control-state">running<' in html


def test_home_page_action_queue_links_ready_state_to_real_status_anchor() -> None:
    settings = RuntimeSettings()
    readiness = PreflightReport(profile="paper", blocked=False, checks=())
    html = render_home_page(
        settings=settings,
        logs=(),
        runtime=HomeRuntimeContext(readiness=readiness),
    )

    assert 'id="status" class="status-strip"' in html
    assert 'data-testid="action-queue"' in html
    assert 'href="#status"' in html
    assert "Paper/testnet runtime is ready" in html


def test_home_page_action_queue_links_support_bundle_to_export_endpoint() -> None:
    settings = RuntimeSettings()
    readiness = PreflightReport(profile="paper", blocked=False, checks=())
    html = render_home_page(
        settings=settings,
        logs=initial_log_entries(),
        runtime=HomeRuntimeContext(readiness=readiness),
    )

    assert 'data-testid="action-queue"' in html
    assert 'href="/logs"' in html
    assert 'href="/api/v1/reports/support-bundle.zip"' in html
    assert "Export a support bundle if errors persist" in html


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
    assert 'name="risk_profile"' in setup_html
    assert 'name="permission_withdrawal"' in setup_html
    assert 'name="api_key" type="password"' in setup_html
    assert 'name="api_secret" type="password"' in setup_html
    assert 'name="exchange.name"' in simple_html
    assert 'name="exchange.trading_mode"' in simple_html
    assert 'name="ui.locale"' in simple_html
    assert '<option value="en" selected>English</option>' in simple_html
    assert '<option value="ko">한국어</option>' in simple_html
    assert '<option value="el">Ελληνικά</option>' in simple_html
    assert 'name="risk.stake_usdt"' in simple_html
    assert 'name="risk.max_open_trades"' in simple_html


def test_settings_page_renders_first_run_wizard_in_operator_order() -> None:
    # Given: default local runtime settings.
    settings = RuntimeSettings()

    # When: the first-run setup wizard is rendered.
    html = render_settings_page(settings=settings)

    # Then: the operator path follows the agreed safe order.
    markers = (
        'data-testid="setup-step-exchange"',
        'data-testid="setup-step-api-key"',
        'data-testid="setup-step-api-secret"',
        'data-testid="setup-step-permission-audit"',
        'data-testid="setup-step-leverage"',
        'data-testid="setup-step-risk-profile"',
        'data-testid="setup-step-wallet-balance"',
        'data-testid="setup-step-allocated-amount"',
        'data-testid="setup-step-market-mode"',
        'data-testid="setup-step-intent"',
    )
    positions = tuple(html.index(marker) for marker in markers)
    assert positions == tuple(sorted(positions))
    assert 'data-testid="wallet-fetch-button"' in html
    assert 'name="allocated_amount_usdt"' in html
    assert 'name="permission_withdrawal"' in html
    assert 'name="risk_profile"' in html
    assert 'data-testid="setup-recommended-leverage">3x<' in html
    assert '<option value="paper" selected>Dry-run</option>' in html
    assert "wallet seed" not in html.lower()
    assert "private key" not in html.lower()


def test_settings_page_renders_developer_update_states_without_network_action() -> None:
    # Given: local settings.
    settings = RuntimeSettings()

    # When: Settings renders the update panel.
    html = render_settings_page(settings=settings)

    # Then: one-click update states are visible but no remote fetch is embedded in HTML.
    assert 'data-testid="settings-update-panel"' in html
    assert 'data-testid="update-preview-state"' in html
    assert 'data-testid="update-apply-state"' in html
    assert 'data-testid="update-rollback-state"' in html
    assert 'data-testid="update-preview-button"' in html
    assert 'data-testid="update-apply-button"' in html
    assert 'data-testid="update-rollback-button"' in html
    assert 'data-testid="update-backup-reference"' in html
    assert 'data-testid="update-acknowledge-unverified"' in html
    assert "engine + strategy" in html
    assert "https://" not in html


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
    assert 'data-testid="pause-button" disabled' in html
    assert 'data-testid="resume-button" disabled' in html
    assert 'data-testid="stop-button" disabled' in html
    assert "Read-only mode blocks changes" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html


def test_read_only_home_page_disables_runtime_controls() -> None:
    settings = RuntimeSettings(ui=UiSettings(read_only=True))

    html = render_home_page(settings=settings, logs=initial_log_entries())

    assert 'data-testid="start-button" disabled' in html
    assert 'data-testid="pause-button" disabled' in html
    assert 'data-testid="resume-button" disabled' in html
    assert 'data-testid="stop-button" disabled' in html


def test_home_page_uses_configured_locale_in_document_lang() -> None:
    # Given: Korean frontend settings.
    settings = RuntimeSettings(ui=UiSettings(locale=Locale.KO))

    # When: the home page is rendered.
    html = render_home_page(settings=settings, logs=initial_log_entries())

    # Then: document language changes without altering stable test ids.
    assert '<html lang="ko">' in html
    assert 'data-testid="home-root"' in html
