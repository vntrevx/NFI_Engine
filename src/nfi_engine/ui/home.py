from __future__ import annotations

from decimal import Decimal
from html import escape

from nfi_engine.api.models import LogEntryResponse
from nfi_engine.config import Locale, LogLevel, RuntimeSettings
from nfi_engine.dashboard import (
    DashboardReadModels,
    build_dashboard_actions,
    summarize_dashboard_read_models,
)
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.ui.chart import render_dashboard_chart_panel
from nfi_engine.ui.home_actions import render_action_queue
from nfi_engine.ui.home_cockpit import render_home_cockpit
from nfi_engine.ui.home_context import HomeRuntimeContext
from nfi_engine.ui.home_execution import render_execution_safety_signals
from nfi_engine.ui.home_portfolio import render_portfolio_summary
from nfi_engine.ui.i18n import format_message, localize
from nfi_engine.ui.i18n_keys import MessageKey
from nfi_engine.ui.runtime_controls import render_runtime_controls
from nfi_engine.ui.x7_status import render_x7_semantic_status

PAIR_PREVIEW_LIMIT = 4


def render_home_body(
    *,
    settings: RuntimeSettings,
    logs: tuple[LogEntryResponse, ...],
    runtime: HomeRuntimeContext | None = None,
    nav: str,
) -> str:
    locale = settings.ui.locale
    resolved_runtime = runtime or HomeRuntimeContext()
    pairs = _pairs(settings)
    errors = tuple(log for log in logs if log.level is LogLevel.ERROR)
    read_models = resolved_runtime.read_models or DashboardReadModels.empty()
    summary = summarize_dashboard_read_models(
        read_models,
    )
    actions = build_dashboard_actions(
        settings=settings,
        readiness=resolved_runtime.readiness,
        logs=logs,
    )
    x7_status = (
        resolved_runtime.runtime_health.x7_semantic_status
        if resolved_runtime.runtime_health is not None
        else None
    )
    mode = _mode(settings, locale=locale)
    bot_state_metric = _metric(
        "bot-state",
        localize(locale, MessageKey.HOME_METRIC_BOT_STATE),
        resolved_runtime.bot_state.value,
    )
    portfolio = render_portfolio_summary(
        summary,
        read_models=read_models,
        locale=locale,
    )
    chart = render_dashboard_chart_panel(
        exchange=settings.exchange.name,
        trading_mode=settings.exchange.trading_mode.value,
        locale=locale,
    )
    cockpit = render_home_cockpit(
        settings=settings,
        logs=logs,
        actions=actions,
        locale=locale,
        runtime=resolved_runtime,
    )
    return (
        '<main data-testid="home-root">\n'
        "  <header>\n"
        "    <div>\n"
        "      <h1>NFI Engine</h1>\n"
        f"      <p>{localize(locale, MessageKey.HOME_SUBTITLE)}</p>\n"
        "    </div>\n"
        f"    {nav}\n"
        "  </header>\n"
        '  <div id="status" class="status-strip" data-testid="mode-strip">\n'
        f"    {bot_state_metric}\n"
        f"    {
            _metric(
                'exchange-mode',
                localize(locale, MessageKey.HOME_METRIC_MODE),
                mode,
            )
        }\n"
        f"    {
            _metric(
                'open-trades',
                localize(locale, MessageKey.HOME_METRIC_OPEN_TRADES),
                str(summary.open_trades),
            )
        }\n"
        f"    {
            _metric(
                'session-pnl',
                localize(locale, MessageKey.HOME_METRIC_SESSION_PNL),
                _format_usdt(summary.session_profit),
            )
        }\n"
        "  </div>\n"
        '  <div class="dashboard-grid" data-testid="dashboard-grid">\n'
        '    <div class="dashboard-primary-stack" data-testid="dashboard-primary-stack">\n'
        f"{portfolio}\n"
        f"{chart}\n"
        f"    {render_execution_safety_signals(locale=locale)}\n"
        "    </div>\n"
        '    <aside class="dashboard-ops-rail" data-testid="dashboard-ops-rail">\n'
        f"{cockpit}\n"
        f"    {
            render_runtime_controls(
                settings=settings,
                locale=locale,
                state=resolved_runtime.bot_state,
            )
        }\n"
        f"{render_x7_semantic_status(x7_status, locale=locale)}"
        f"    {render_action_queue(actions, locale=locale)}\n"
        f"    {_setup_doctor(resolved_runtime.readiness, locale=locale)}\n"
        f"    {_pairlist_summary(pairs, locale=locale)}\n"
        f"    {_recent_errors(errors, locale=locale)}\n"
        "    </aside>\n"
        "  </div>\n"
        "</main>\n"
    )


def _metric(test_id: str, label: str, value: str) -> str:
    return (
        f'<div class="metric" data-testid="{escape(test_id)}">'
        f"<span>{escape(label)}</span><strong>{escape(value)}</strong></div>"
    )


def _format_usdt(value: Decimal) -> str:
    return f"{value:.2f} USDT"


def _mode(settings: RuntimeSettings, *, locale: Locale) -> str:
    mode = settings.exchange.trading_mode.value
    venue = (
        localize(locale, MessageKey.HOME_VALUE_TESTNET)
        if settings.exchange.testnet
        else localize(locale, MessageKey.HOME_VALUE_LIVE_VENUE)
    )
    return f"{mode} / {venue}"


def _setup_doctor(readiness: PreflightReport | None, *, locale: Locale) -> str:
    status = _readiness_status(readiness, locale=locale)
    return (
        '<section data-testid="setup-doctor">\n'
        f"  <h2>{localize(locale, MessageKey.HOME_SETUP_DOCTOR)}</h2>\n"
        f'  <div class="state">{escape(status)}</div>\n'
        f"  {_readiness_list(readiness, locale=locale)}\n"
        "</section>\n"
    )


def _pairlist_summary(pairs: tuple[str, ...], *, locale: Locale) -> str:
    preview = ", ".join(pairs[:PAIR_PREVIEW_LIMIT])
    if len(pairs) > PAIR_PREVIEW_LIMIT:
        preview = f"{preview}, +{len(pairs) - PAIR_PREVIEW_LIMIT}"
    if preview == "":
        preview = localize(locale, MessageKey.COMMON_NONE)
    count = format_message(locale, MessageKey.HOME_CONFIGURED_PAIRS, count=len(pairs))
    return (
        '<section data-testid="pairlist-summary">\n'
        f"  <h2>{localize(locale, MessageKey.HOME_PAIRLIST)}</h2>\n"
        f'  <div class="state">{count}</div>\n'
        f"  <p>{escape(preview)}</p>\n"
        "</section>\n"
    )


def _recent_errors(errors: tuple[LogEntryResponse, ...], *, locale: Locale) -> str:
    rows = "\n".join(_error_row(log) for log in errors[:3])
    if rows == "":
        rows = f'<li class="muted">{localize(locale, MessageKey.COMMON_NONE)}</li>'
    return (
        '<section data-testid="recent-errors">\n'
        f"  <h2>{localize(locale, MessageKey.HOME_RECENT_ERRORS)}</h2>\n"
        f"  <ul>{rows}</ul>\n"
        f'  <a href="/logs">{localize(locale, MessageKey.OPEN_LOGS)}</a>\n'
        "</section>\n"
    )


def _readiness_status(readiness: PreflightReport | None, *, locale: Locale) -> str:
    if readiness is None:
        return localize(locale, MessageKey.READINESS_EMPTY)
    if readiness.blocked:
        return localize(locale, MessageKey.COMMON_BLOCKED)
    return localize(locale, MessageKey.COMMON_READY)


def _readiness_list(readiness: PreflightReport | None, *, locale: Locale) -> str:
    if readiness is None:
        prompt = localize(locale, MessageKey.HOME_PREFLIGHT_PROMPT)
        return f'<ul><li class="muted">{prompt}</li></ul>'
    rows = "\n".join(
        f"<li>{escape(check.code.value)}: {escape(check.status.value)}</li>"
        for check in readiness.checks[:4]
    )
    return f"<ul>{rows}</ul>"


def _error_row(log: LogEntryResponse) -> str:
    return f"<li><strong>{escape(log.code)}</strong> {escape(log.safe_summary)}</li>"


def _pairs(settings: RuntimeSettings) -> tuple[str, ...]:
    return tuple(pair.strip() for pair in settings.pairlist.whitelist.split(",") if pair.strip())
