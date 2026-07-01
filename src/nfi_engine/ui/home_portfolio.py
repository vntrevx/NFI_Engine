from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import assert_never

from nfi_engine.config import Locale
from nfi_engine.dashboard import (
    DashboardOpenPosition,
    DashboardOperatorSummary,
    DashboardReadModels,
    DashboardRecentTrade,
    DashboardRiskPressure,
)
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey

POSITION_PREVIEW_LIMIT = 3
TRADE_PREVIEW_LIMIT = 3


def render_portfolio_summary(
    summary: DashboardOperatorSummary,
    *,
    read_models: DashboardReadModels,
    locale: Locale,
) -> str:
    pressure = _risk_pressure_label(summary.risk_pressure, locale=locale)
    pressure_class = f"portfolio-pressure-{summary.risk_pressure.value}"
    closed_detail = (
        f"{summary.closed_trades} {localize(locale, MessageKey.HOME_OVERVIEW_CLOSED_TRADES)}"
    )
    return (
        '<section class="portfolio-panel home-overview" data-testid="portfolio-summary">\n'
        '  <div class="section-heading">\n'
        "    <div>\n"
        f"      <h2>{localize(locale, MessageKey.HOME_OVERVIEW_TITLE)}</h2>\n"
        f"      <p>{localize(locale, MessageKey.HOME_OVERVIEW_DESCRIPTION)}</p>\n"
        "    </div>\n"
        f'    <strong class="{escape(pressure_class)}" '
        'data-testid="portfolio-risk-pressure" '
        f'data-dashboard-field="risk-pressure-badge">{escape(pressure)}</strong>\n'
        "  </div>\n"
        '  <div class="overview-grid">\n'
        f"    {
            _overview_cell(
                'overview-positions',
                'open-positions',
                localize(locale, MessageKey.HOME_METRIC_OPEN_TRADES),
                str(summary.open_trades),
                localize(locale, MessageKey.HOME_OVERVIEW_POSITIONS_DETAIL),
            )
        }\n"
        f"    {
            _overview_cell(
                'overview-pnl',
                'session-pnl',
                localize(locale, MessageKey.HOME_METRIC_SESSION_PNL),
                _format_usdt(summary.session_profit),
                closed_detail,
            )
        }\n"
        f"    {
            _overview_cell(
                'overview-exposure',
                'exposure-pct',
                localize(locale, MessageKey.HOME_PORTFOLIO_EXPOSURE_PCT),
                _format_pct(summary.exposure_pct),
                _format_usdt(summary.gross_exposure),
            )
        }\n"
        f"    {
            _overview_cell(
                'overview-equity',
                'account-equity',
                localize(locale, MessageKey.HOME_PORTFOLIO_ACCOUNT_EQUITY),
                _format_usdt(summary.account_equity),
                _format_available(summary.account_available, locale=locale),
            )
        }\n"
        f"    {
            _overview_cell(
                'overview-risk',
                'risk-pressure',
                localize(locale, MessageKey.HOME_PORTFOLIO_RISK_PRESSURE),
                pressure,
                _format_leverage(summary.average_leverage),
            )
        }\n"
        "  </div>\n"
        '  <div class="overview-split">\n'
        f"    {_position_preview(read_models.open_positions, locale=locale)}\n"
        f"    {_trade_preview(read_models.recent_trades, locale=locale)}\n"
        "  </div>\n"
        "</section>"
    )


def _overview_cell(
    test_id: str,
    field: str,
    label: str,
    value: str,
    detail: str,
) -> str:
    return (
        f'<div class="overview-cell" data-testid="{escape(test_id)}">'
        f"<span>{escape(label)}</span>"
        f'<strong data-dashboard-field="{escape(field)}">{escape(value)}</strong>'
        f'<small data-dashboard-field="{escape(field)}-detail">{escape(detail)}</small>'
        "</div>"
    )


def _position_preview(
    positions: tuple[DashboardOpenPosition, ...],
    *,
    locale: Locale,
) -> str:
    rows = "\n".join(_position_row(position) for position in positions[:POSITION_PREVIEW_LIMIT])
    if rows == "":
        rows = f'<li class="muted">{localize(locale, MessageKey.HOME_OVERVIEW_NO_POSITIONS)}</li>'
    return (
        '<div class="overview-list" data-testid="overview-position-panel">\n'
        f"  <h3>{localize(locale, MessageKey.HOME_OVERVIEW_POSITIONS)}</h3>\n"
        f'  <ul data-dashboard-field="position-list">{rows}</ul>\n'
        "</div>"
    )


def _trade_preview(
    trades: tuple[DashboardRecentTrade, ...],
    *,
    locale: Locale,
) -> str:
    rows = "\n".join(_trade_row(trade) for trade in trades[:TRADE_PREVIEW_LIMIT])
    if rows == "":
        rows = f'<li class="muted">{localize(locale, MessageKey.HOME_OVERVIEW_NO_TRADES)}</li>'
    return (
        '<div class="overview-list" data-testid="overview-pnl-panel">\n'
        f"  <h3>{localize(locale, MessageKey.HOME_OVERVIEW_RECENT_PNL)}</h3>\n"
        f'  <ul data-dashboard-field="trade-list">{rows}</ul>\n'
        "</div>"
    )


def _position_row(position: DashboardOpenPosition) -> str:
    detail = (
        f"{position.side.value} {_format_decimal(position.quantity)} @ "
        f"{_format_decimal(position.entry_price)} | {_format_leverage(position.leverage)}"
    )
    return (
        '<li data-testid="overview-position">'
        f"<strong>{escape(position.pair)}</strong>"
        f"<span>{escape(detail)}</span>"
        "</li>"
    )


def _trade_row(trade: DashboardRecentTrade) -> str:
    detail = f"{trade.state.value} | {_format_usdt(trade.profit)}"
    return (
        '<li data-testid="overview-trade">'
        f"<strong>{escape(trade.pair)}</strong>"
        f"<span>{escape(detail)}</span>"
        "</li>"
    )


def _risk_pressure_label(pressure: DashboardRiskPressure, *, locale: Locale) -> str:
    match pressure:
        case DashboardRiskPressure.IDLE:
            return localize(locale, MessageKey.HOME_PORTFOLIO_RISK_IDLE)
        case DashboardRiskPressure.BALANCED:
            return localize(locale, MessageKey.HOME_PORTFOLIO_RISK_BALANCED)
        case DashboardRiskPressure.ELEVATED:
            return localize(locale, MessageKey.HOME_PORTFOLIO_RISK_ELEVATED)
        case unreachable:
            assert_never(unreachable)


def _format_usdt(value: Decimal) -> str:
    return f"{value:.2f} USDT"


def _format_pct(value: Decimal) -> str:
    return f"{value:.1f}%"


def _format_leverage(value: Decimal) -> str:
    return f"{value:.1f}x"


def _format_available(value: Decimal, *, locale: Locale) -> str:
    return f"{localize(locale, MessageKey.HOME_PORTFOLIO_AVAILABLE)} {_format_usdt(value)}"


def _format_decimal(value: Decimal) -> str:
    rendered = format(value.normalize(), "f")
    return "0" if rendered == "-0" else rendered
