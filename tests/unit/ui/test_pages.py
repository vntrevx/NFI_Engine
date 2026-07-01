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


def _react_shell(html: str) -> bool:
    return 'id="nfi-react-root"' in html


def _assert_react_shell(html: str, *, page: str) -> None:
    assert f'data-nfi-page="{page}"' in html
    assert 'id="nfi-react-root"' in html
    assert "/ui-react/assets/" in html
    assert 'meta name="nfi-csrf-token"' in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "https://" not in html
    assert "cdn" not in html.lower()


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

    if _react_shell(html):
        _assert_react_shell(html, page="home")
        return

    required_markers = (
        'data-testid="home-root"',
        'data-testid="home-nav"',
        'data-testid="dashboard-grid"',
        'data-testid="dashboard-primary-stack"',
        'data-testid="dashboard-ops-rail"',
        'data-testid="setup-doctor"',
        'data-testid="home-chart-shell"',
        'data-testid="dashboard-chart"',
        'data-testid="chart-status"',
        'data-testid="chart-render-time"',
        'data-poll-ms="5000"',
        'data-testid="portfolio-summary"',
        'data-testid="overview-positions"',
        'data-testid="overview-pnl"',
        'data-testid="overview-exposure"',
        'data-testid="overview-equity"',
        'data-testid="overview-risk"',
        'data-testid="overview-position-panel"',
        'data-testid="overview-pnl-panel"',
        'data-dashboard-field="risk-pressure"',
        'data-testid="operator-cockpit"',
        'data-testid="cockpit-capability-level"',
        'data-testid="cockpit-runtime-health"',
        'data-testid="cockpit-wallet-balance"',
        'data-testid="cockpit-leverage"',
        'data-testid="cockpit-permission-audit"',
        'data-testid="cockpit-latest-error"',
        'data-testid="cockpit-next-action"',
        'data-testid="pairlist-summary"',
        'data-testid="recent-errors"',
        'data-testid="action-queue"',
        'data-testid="action-item"',
        'data-testid="execution-safety-signals"',
        'data-testid="execution-signal-order_lifecycle"',
        'data-testid="execution-signal-partial_fill_exposure"',
        'data-testid="runtime-controls"',
        'data-testid="runtime-control-state"',
        'data-testid="pause-button"',
        'data-testid="resume-button"',
        'data-command="start"',
        'data-command="pause"',
        'data-command="resume"',
        'data-command="stop"',
        "/api/v1/dashboard/snapshot",
        "Runtime health",
        "Operator command center",
    )
    removed_markers = (
        'data-testid="cockpit-active-mode"',
        'data-testid="cockpit-allocated-amount"',
        'data-testid="cockpit-risk-profile"',
        'data-testid="cockpit-where-next"',
        "chart-bars",
        "localStorage",
        "sessionStorage",
    )
    for marker in required_markers:
        assert marker in html
    for marker in removed_markers:
        assert marker not in html
    assert "landing" not in html.lower()
    assert "https://" not in html
    assert "cdn" not in html.lower()


def test_home_page_uses_runtime_context_bot_state_for_metric_and_control_state() -> None:
    settings = RuntimeSettings()
    html = render_home_page(
        settings=settings,
        logs=(),
        runtime=HomeRuntimeContext(bot_state=BotState.RUNNING),
    )

    if _react_shell(html):
        _assert_react_shell(html, page="home")
        return

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

    if _react_shell(html):
        _assert_react_shell(html, page="home")
        return

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

    if _react_shell(html):
        _assert_react_shell(html, page="home")
        return

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

    if _react_shell(html):
        _assert_react_shell(html, page="logs")
        return

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

    if _react_shell(html):
        _assert_react_shell(html, page="home")
        return

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
    assert '<html lang="ko"' in html
    if _react_shell(html):
        _assert_react_shell(html, page="home")
    else:
        assert 'data-testid="home-root"' in html
