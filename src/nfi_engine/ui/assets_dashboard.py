from __future__ import annotations

from typing import Final

DASHBOARD_STYLE: Final = """
.chart-panel {
  min-height: 312px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 14px;
  border-color: var(--line-strong);
  background:
    linear-gradient(180deg, rgb(255 255 255 / .92), rgb(249 251 250 / .96)),
    var(--panel);
}
.chart-heading, .chart-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.chart-heading span, .muted {
  color: var(--muted);
  font-size: 12px;
}
.chart-canvas-wrap {
  min-height: 210px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background:
    repeating-linear-gradient(0deg, rgb(22 32 28 / .045) 0 1px, transparent 1px 42px),
    repeating-linear-gradient(90deg, rgb(22 32 28 / .035) 0 1px, transparent 1px 58px),
    var(--panel-subtle);
  overflow: hidden;
  box-shadow: 0 1px 0 rgb(255 255 255 / .9) inset;
}
.chart-canvas-wrap canvas {
  display: block;
  width: 100%;
  height: 220px;
}
.chart-panel[data-chart-state="error"] .state {
  border-left-color: var(--danger);
  background: var(--danger-soft);
}
.chart-panel[data-chart-state="stale"] .state,
.chart-panel[data-chart-state="empty"] .state {
  border-left-color: var(--warn);
  background: var(--warn-soft);
}
.portfolio-panel {
  grid-column: 1 / -1;
}
.home-overview {
  position: relative;
  overflow: hidden;
  border-color: var(--command-line);
  background:
    radial-gradient(circle at 92% 0, rgb(15 118 110 / .32), transparent 26rem),
    linear-gradient(135deg, rgb(255 255 255 / .08), rgb(255 255 255 / 0) 48%),
    var(--command);
  color: var(--command-text);
}
.home-overview::before {
  position: absolute;
  inset: 0;
  background:
    repeating-linear-gradient(90deg, rgb(255 255 255 / .035) 0 1px, transparent 1px 70px),
    repeating-linear-gradient(0deg, rgb(255 255 255 / .025) 0 1px, transparent 1px 54px);
  content: "";
  pointer-events: none;
}
.home-overview > * {
  position: relative;
}
.home-overview .section-heading h2 {
  color: var(--command-text);
}
.home-overview .section-heading p {
  color: var(--command-muted);
}
.home-overview .section-heading strong {
  border-color: var(--command-line);
  border-radius: 5px;
  background: var(--command-elevated);
  color: var(--command-text);
}
.overview-grid {
  display: grid;
  grid-template-columns: 1.05fr 1.15fr 1fr 1.1fr .9fr;
  gap: 10px;
}
.overview-cell {
  min-width: 0;
  min-height: 108px;
  display: grid;
  align-content: space-between;
  gap: 7px;
  padding: 12px;
  border: 1px solid var(--command-line);
  border-radius: 6px;
  background:
    linear-gradient(180deg, rgb(255 255 255 / .055), rgb(255 255 255 / .018)),
    var(--command-elevated);
  box-shadow: 0 1px 0 rgb(255 255 255 / .08) inset;
}
.overview-cell span {
  display: block;
  color: var(--command-muted);
  font-size: 12px;
}
.overview-cell strong {
  display: block;
  color: var(--command-text);
  font-size: 22px;
  line-height: 1.1;
  overflow-wrap: anywhere;
}
.overview-cell[data-testid="overview-pnl"] strong {
  color: var(--accent-soft);
}
.overview-cell[data-testid="overview-exposure"] strong {
  color: var(--warn-soft);
}
.overview-cell small {
  display: block;
  min-height: 16px;
  color: var(--command-muted);
  font-size: 12px;
  line-height: 1.25;
  overflow-wrap: anywhere;
}
.overview-split {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}
.overview-list {
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid var(--command-line);
  border-radius: 6px;
  background:
    linear-gradient(180deg, rgb(255 255 255 / .05), rgb(255 255 255 / .018)),
    var(--command-elevated);
  box-shadow: 0 1px 0 rgb(255 255 255 / .08) inset;
}
.overview-list h3 {
  margin: 0 0 8px;
  color: var(--command-text);
  font-size: 13px;
  line-height: 1.2;
  letter-spacing: 0;
}
.overview-list ul {
  display: grid;
  gap: 5px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.overview-list li {
  min-height: 27px;
  display: grid;
  grid-template-columns: minmax(0, .7fr) minmax(0, 1fr);
  gap: 8px;
  align-items: center;
  border-top: 1px solid var(--command-line);
  padding-top: 5px;
}
.overview-list li:first-child {
  border-top: 0;
  padding-top: 0;
}
.overview-list strong,
.overview-list span {
  min-width: 0;
  overflow-wrap: anywhere;
}
.overview-list strong { font-size: 12px; }
.overview-list span {
  color: var(--command-muted);
  font-size: 12px;
  text-align: right;
}
.overview-list .muted {
  color: var(--command-muted);
}
.portfolio-pressure-idle { border-color: var(--command-line); }
.portfolio-pressure-balanced {
  border-color: var(--accent);
  background: rgb(15 118 110 / .22);
  color: var(--accent-soft);
}
.portfolio-pressure-elevated {
  border-color: var(--warn);
  background: rgb(154 103 0 / .18);
  color: var(--warn-soft);
}
.signal-list {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  list-style: none;
  margin: 12px 0 0;
  padding: 0;
}
.signal-list li {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel-subtle);
}
.signal-list strong,
.signal-list span {
  overflow-wrap: anywhere;
}
.signal-list span {
  color: var(--muted);
  font-size: 12px;
}
@media (max-width: 780px) {
  .chart-heading, .chart-footer { display: block; }
  .chart-heading span, .chart-footer .muted { display: block; margin-top: 8px; }
  .overview-grid, .overview-split { grid-template-columns: 1fr; }
  .overview-list li { grid-template-columns: 1fr; }
  .overview-list span { text-align: left; }
  .signal-list { grid-template-columns: 1fr; }
}
"""

DASHBOARD_SCRIPT: Final = """
<script>
(() => {
  const root = document.querySelector('[data-testid="home-chart-shell"]');
  if (!root) {
    return;
  }
  const canvas = root.querySelector('[data-testid="dashboard-chart"]');
  const status = root.querySelector('[data-testid="chart-status"]');
  const timing = root.querySelector('[data-testid="chart-render-time"]');
  const pollMs = Number.parseInt(root.dataset.pollMs || '5000', 10);
  const staleMs = Math.max(pollMs * 3, 15000);
  let lastSuccessAt = 0;
  const msg = (key, fallback) => window.NFI_I18N?.[key] || fallback;

  function setStatus(state, message) {
    root.dataset.chartState = state;
    status.textContent = message;
  }

  function numberFrom(value) {
    const parsed = Number.parseFloat(String(value));
    return Number.isFinite(parsed) ? parsed : null;
  }

  function money(value) {
    const numeric = Number.isFinite(value) ? value : 0;
    return `${numeric.toFixed(2)} USDT`;
  }

  function pct(value) {
    const numeric = Number.isFinite(value) ? value : 0;
    return `${numeric.toFixed(1)}%`;
  }

  function leverage(value) {
    const numeric = Number.isFinite(value) ? value : 0;
    return `${numeric.toFixed(1)}x`;
  }

  function field(name) {
    return document.querySelector(`[data-dashboard-field="${name}"]`);
  }

  function setField(name, value) {
    const target = field(name);
    if (target) {
      target.textContent = value;
    }
  }

  function setMetric(testId, value) {
    const target = document.querySelector(`[data-testid="${testId}"] strong`);
    if (target) {
      target.textContent = value;
    }
  }

  function exposureOf(position) {
    const quantity = Math.abs(numberFrom(position.quantity) || 0);
    const entry = numberFrom(position.entry_price) || 0;
    const multiplier = numberFrom(position.leverage) || 1;
    return quantity * entry * multiplier;
  }

  function summarize(payload) {
    const positions = Array.isArray(payload.open_positions) ? payload.open_positions : [];
    const trades = Array.isArray(payload.recent_trades) ? payload.recent_trades : [];
    const equityPoints = Array.isArray(payload.equity_points) ? payload.equity_points : [];
    const latestEquity = equityPoints.length > 0 ? equityPoints[equityPoints.length - 1] : {};
    const equity = numberFrom(latestEquity.equity) || 0;
    const available = numberFrom(latestEquity.available) || 0;
    const exposure = positions.reduce((total, position) => total + exposureOf(position), 0);
    const exposurePct = equity > 0 ? (exposure / equity) * 100 : 0;
    const sessionPnl = trades.reduce((total, trade) => total + (numberFrom(trade.profit) || 0), 0);
    const closedTrades = trades.filter((trade) => String(trade.state) === 'closed').length;
    const avgLeverage = positions.length === 0
      ? 0
      : positions.reduce(
        (total, position) => total + (numberFrom(position.leverage) || 0),
        0,
      ) / positions.length;
    const risk = exposure <= 0
      ? 'idle'
      : (equity <= 0 || exposurePct > 100 ? 'elevated' : 'balanced');
    return {
      positions,
      trades,
      equity,
      available,
      exposure,
      exposurePct,
      sessionPnl,
      closedTrades,
      avgLeverage,
      risk,
    };
  }

  function row(primary, secondary, testId) {
    const item = document.createElement('li');
    item.dataset.testid = testId;
    const strong = document.createElement('strong');
    const span = document.createElement('span');
    strong.textContent = primary;
    span.textContent = secondary;
    item.append(strong, span);
    return item;
  }

  function replaceList(name, items, emptyText) {
    const target = field(name);
    if (!target) {
      return;
    }
    target.replaceChildren(...(items.length > 0 ? items : [row(emptyText, '', 'overview-empty')]));
  }

  function updateOverview(payload) {
    const data = summarize(payload);
    const riskLabel = msg(`home.portfolio_risk_${data.risk}`, data.risk);
    setField('open-positions', String(data.positions.length));
    setField('open-positions-detail', msg('home.overview_positions_detail', 'live exposure lane'));
    setField('session-pnl', money(data.sessionPnl));
    setField(
      'session-pnl-detail',
      `${data.closedTrades} ${msg('home.overview_closed_trades', 'closed')}`,
    );
    setField('exposure-pct', pct(data.exposurePct));
    setField('exposure-pct-detail', money(data.exposure));
    setField('account-equity', money(data.equity));
    setField(
      'account-equity-detail',
      `${msg('home.portfolio_available', 'Available')} ${money(data.available)}`,
    );
    setField('risk-pressure', riskLabel);
    setField('risk-pressure-detail', leverage(data.avgLeverage));
    setField('risk-pressure-badge', riskLabel);
    setMetric('open-trades', String(data.positions.length));
    setMetric('session-pnl', money(data.sessionPnl));
    const riskBadge = field('risk-pressure-badge') || field('risk-pressure');
    if (riskBadge) {
      riskBadge.classList.remove(
        'portfolio-pressure-idle',
        'portfolio-pressure-balanced',
        'portfolio-pressure-elevated',
      );
      riskBadge.classList.add(`portfolio-pressure-${data.risk}`);
    }
    replaceList(
      'position-list',
      data.positions.slice(0, 3).map((position) => row(
        String(position.pair || '-'),
        `${position.side || '-'} ${position.quantity || '0'} @ `
          + `${position.entry_price || '0'} | `
          + leverage(numberFrom(position.leverage) || 0),
        'overview-position',
      )),
      msg('home.overview_no_positions', 'No open positions.'),
    );
    replaceList(
      'trade-list',
      data.trades.slice(0, 3).map((trade) => row(
        String(trade.pair || '-'),
        `${trade.state || '-'} | ${money(numberFrom(trade.profit) || 0)}`,
        'overview-trade',
      )),
      msg('home.overview_no_trades', 'No recent PnL events.'),
    );
  }

  function pointFromPrice(point) {
    const value = numberFrom(point.price);
    return value === null ? null : {at: String(point.at), value, label: String(point.pair)};
  }

  function pointFromEquity(point) {
    const value = numberFrom(point.equity);
    return value === null ? null : {at: String(point.at), value, label: 'equity'};
  }

  function readSeries(payload) {
    const prices = Array.isArray(payload.price_points) ? payload.price_points : [];
    const equities = Array.isArray(payload.equity_points) ? payload.equity_points : [];
    const raw = prices.length > 0 ? prices.map(pointFromPrice) : equities.map(pointFromEquity);
    return raw.filter((point) => point !== null);
  }

  function resizeContext(context) {
    const ratio = window.devicePixelRatio || 1;
    const width = Math.max(320, Math.round(canvas.getBoundingClientRect().width));
    const height = 240;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    return {width, height};
  }

  function chartColor(name, fallback) {
    const value = getComputedStyle(root).getPropertyValue(name).trim();
    return value || fallback;
  }

  function paintChartBase(context, frame) {
    context.clearRect(0, 0, frame.width, frame.height);
    context.fillStyle = chartColor('--panel-subtle', '#f9fbfa');
    context.fillRect(0, 0, frame.width, frame.height);
    context.strokeStyle = chartColor('--line', '#c8d5cf');
    context.lineWidth = 1;
    context.globalAlpha = 0.8;
    for (const level of [0.2, 0.4, 0.6, 0.8]) {
      const y = 18 + (frame.height - 56) * level;
      context.beginPath();
      context.moveTo(24, y);
      context.lineTo(frame.width - 20, y);
      context.stroke();
    }
    for (const level of [0.2, 0.4, 0.6, 0.8]) {
      const x = 24 + (frame.width - 44) * level;
      context.beginPath();
      context.moveTo(x, 18);
      context.lineTo(x, frame.height - 38);
      context.stroke();
    }
    context.globalAlpha = 1;
    context.strokeStyle = chartColor('--line-strong', '#a9bbb2');
    context.beginPath();
    context.moveTo(24, frame.height - 40);
    context.lineTo(frame.width - 20, frame.height - 40);
    context.stroke();
  }

  function drawEmpty(context, frame) {
    paintChartBase(context, frame);
    context.strokeStyle = chartColor('--accent', '#0f766e');
    context.setLineDash([6, 7]);
    context.beginPath();
    context.moveTo(24, frame.height - 96);
    context.lineTo(frame.width - 20, frame.height - 96);
    context.stroke();
    context.setLineDash([]);
    canvas.dataset.renderedPoints = '0';
    canvas.dataset.chartNonblank = 'false';
  }

  function drawSeries(context, frame, points) {
    const started = performance.now();
    const values = points.map((point) => point.value);
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max === min ? 1 : max - min;
    const left = 28;
    const right = frame.width - 20;
    const top = 18;
    const bottom = frame.height - 40;
    paintChartBase(context, frame);
    context.strokeStyle = chartColor('--accent', '#0f766e');
    context.lineWidth = 2.4;
    context.beginPath();
    let lastX = left;
    let lastY = bottom;
    points.forEach((point, index) => {
      const x = points.length === 1 ? left : left + ((right - left) * index) / (points.length - 1);
      const y = bottom - ((point.value - min) / span) * (bottom - top);
      lastX = x;
      lastY = y;
      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    });
    context.stroke();
    context.fillStyle = chartColor('--accent', '#0f766e');
    context.beginPath();
    context.arc(lastX, lastY, 4, 0, Math.PI * 2);
    context.fill();
    context.fillStyle = chartColor('--ink', '#16201c');
    context.font = '12px ui-monospace, SFMono-Regular, Consolas, monospace';
    const last = points[points.length - 1];
    context.fillText(`${last.label} ${last.value.toFixed(4)}`, left, frame.height - 12);
    canvas.dataset.renderedPoints = String(points.length);
    canvas.dataset.chartNonblank = 'true';
    return performance.now() - started;
  }

  function render(payload, payloadBytes) {
    const context = canvas.getContext('2d');
    if (!context) {
      setStatus('error', msg('chart.unavailable', 'Chart canvas is unavailable.'));
      return;
    }
    const frame = resizeContext(context);
    const points = readSeries(payload);
    if (points.length === 0) {
      drawEmpty(context, frame);
      setStatus('empty', msg('chart.empty', 'No equity or price points yet.'));
      timing.textContent = `render 0.0ms / ${payloadBytes}B`;
      return;
    }
    const elapsed = drawSeries(context, frame, points);
    const loaded = msg('chart.points_loaded', '{count} chart points loaded.');
    setStatus('ready', loaded.replace('{count}', String(points.length)));
    timing.textContent = `render ${elapsed.toFixed(1)}ms / ${payloadBytes}B`;
  }

  async function loadSnapshot() {
    setStatus('loading', msg('chart.loading', 'Loading dashboard snapshot.'));
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 2500);
    try {
      const response = await fetch('/api/v1/dashboard/snapshot', {
        credentials: 'same-origin',
        signal: controller.signal
      });
      const text = await response.text();
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = JSON.parse(text);
      updateOverview(payload);
      render(payload, text.length);
      lastSuccessAt = Date.now();
    } catch (error) {
      const stale = lastSuccessAt > 0 && Date.now() - lastSuccessAt > staleMs;
      const message = stale
        ? msg('chart.stale', 'Snapshot is stale.')
        : msg('chart.refresh_failed', 'Snapshot refresh failed.');
      setStatus(stale ? 'stale' : 'error', message);
    } finally {
      window.clearTimeout(timeoutId);
    }
  }

  requestAnimationFrame(() => {
    loadSnapshot();
    window.setInterval(loadSnapshot, pollMs);
  });
})();
</script>
"""
