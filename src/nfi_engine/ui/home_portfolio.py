from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import assert_never

from nfi_engine.config import Locale
from nfi_engine.dashboard import DashboardOperatorSummary, DashboardRiskPressure
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_portfolio_summary(summary: DashboardOperatorSummary, *, locale: Locale) -> str:
    pressure = _risk_pressure_label(summary.risk_pressure, locale=locale)
    pressure_class = f"portfolio-pressure-{summary.risk_pressure.value}"
    return (
        '<section class="portfolio-panel" data-testid="portfolio-summary">\n'
        '  <div class="section-heading">\n'
        "    <div>\n"
        f"      <h2>{localize(locale, MessageKey.HOME_PORTFOLIO_TITLE)}</h2>\n"
        f"      <p>{localize(locale, MessageKey.HOME_PORTFOLIO_RISK_PRESSURE)}</p>\n"
        "    </div>\n"
        f'    <strong class="{escape(pressure_class)}" '
        f'data-testid="portfolio-risk-pressure">{escape(pressure)}</strong>\n'
        "  </div>\n"
        '  <div class="portfolio-grid">\n'
        f"    {
            _portfolio_cell(
                'portfolio-equity',
                localize(locale, MessageKey.HOME_PORTFOLIO_ACCOUNT_EQUITY),
                _format_usdt(summary.account_equity),
            )
        }\n"
        f"    {
            _portfolio_cell(
                'portfolio-available',
                localize(locale, MessageKey.HOME_PORTFOLIO_AVAILABLE),
                _format_usdt(summary.account_available),
            )
        }\n"
        f"    {
            _portfolio_cell(
                'portfolio-exposure',
                localize(locale, MessageKey.HOME_PORTFOLIO_EXPOSURE),
                _format_usdt(summary.gross_exposure),
            )
        }\n"
        f"    {
            _portfolio_cell(
                'portfolio-exposure-pct',
                localize(locale, MessageKey.HOME_PORTFOLIO_EXPOSURE_PCT),
                _format_pct(summary.exposure_pct),
            )
        }\n"
        f"    {
            _portfolio_cell(
                'portfolio-avg-leverage',
                localize(locale, MessageKey.HOME_PORTFOLIO_AVG_LEVERAGE),
                _format_leverage(summary.average_leverage),
            )
        }\n"
        "  </div>\n"
        "</section>"
    )


def _portfolio_cell(test_id: str, label: str, value: str) -> str:
    return (
        f'<div class="portfolio-cell" data-testid="{escape(test_id)}">'
        f"<span>{escape(label)}</span><strong>{escape(value)}</strong></div>"
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
