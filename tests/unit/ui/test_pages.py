from __future__ import annotations

from nfi_engine.api.models import initial_log_entries
from nfi_engine.config import Locale
from nfi_engine.config.models import RuntimeSettings, UiSettings
from nfi_engine.paper import BotState
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.ui.home_context import HomeRuntimeContext
from nfi_engine.ui.pages import (
    render_home_page,
    render_login_page,
    render_logs_page,
)


def test_login_page_uses_operator_account_fields_not_raw_token_prompt() -> None:
    # Given: default local runtime settings.
    settings = RuntimeSettings()

    # When: the login page is rendered.
    html = render_login_page(settings=settings)

    # Then: the operator sees a normal account login while token storage stays hidden.
    assert 'data-testid="login-root"' in html
    assert 'data-testid="login-username"' in html
    assert 'data-testid="login-password"' in html
    assert 'autocomplete="username"' in html
    assert 'autocomplete="current-password"' in html
    assert 'data-testid="login-token"' not in html
    assert "Operator token" not in html
    assert "api.auth_token" not in html


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
