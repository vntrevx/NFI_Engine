from __future__ import annotations

from html import escape
from typing import Final

from nfi_engine.config import Locale
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey

DEFAULT_POLL_MS: Final = 5_000


def render_dashboard_chart_panel(
    *,
    exchange: str,
    trading_mode: str,
    locale: Locale = Locale.EN,
    poll_ms: int = DEFAULT_POLL_MS,
) -> str:
    return f"""
    <section class="chart-panel" data-testid="home-chart-shell" data-poll-ms="{poll_ms}">
      <div class="chart-heading">
        <div>
          <h2>{localize(locale, MessageKey.CHART_TITLE)}</h2>
          <p>{escape(exchange)} {escape(trading_mode)}</p>
        </div>
        <span data-testid="chart-refresh-rate">{poll_ms // 1000}s polling</span>
      </div>
      <div class="chart-canvas-wrap">
        <canvas
          data-testid="dashboard-chart"
          aria-label="dashboard equity and price chart"
          width="720"
          height="220"
        ></canvas>
      </div>
      <div class="chart-footer">
        <div class="state" data-testid="chart-status">
          {localize(locale, MessageKey.CHART_WAITING)}
        </div>
        <div class="muted" data-testid="chart-render-time">render pending / payload pending</div>
      </div>
    </section>
"""
