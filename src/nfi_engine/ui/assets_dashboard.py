from __future__ import annotations

from typing import Final

DASHBOARD_STYLE: Final = """
.chart-panel {
  min-height: 312px;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 14px;
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
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #f8fbfa;
  overflow: hidden;
}
.chart-canvas-wrap canvas {
  display: block;
  width: 100%;
  height: 220px;
}
.chart-panel[data-chart-state="error"] .state {
  border-left-color: var(--danger);
  background: #fff1f0;
}
.chart-panel[data-chart-state="stale"] .state,
.chart-panel[data-chart-state="empty"] .state {
  border-left-color: var(--warn);
  background: #fff8e1;
}
@media (max-width: 780px) {
  .chart-heading, .chart-footer { display: block; }
  .chart-heading span, .chart-footer .muted { display: block; margin-top: 8px; }
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
    const height = 220;
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    return {width, height};
  }

  function drawEmpty(context, frame) {
    context.clearRect(0, 0, frame.width, frame.height);
    context.fillStyle = '#f8fbfa';
    context.fillRect(0, 0, frame.width, frame.height);
    context.strokeStyle = '#ccd6d1';
    context.lineWidth = 1;
    context.beginPath();
    context.moveTo(24, frame.height - 36);
    context.lineTo(frame.width - 20, frame.height - 36);
    context.stroke();
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
    const bottom = frame.height - 34;
    context.clearRect(0, 0, frame.width, frame.height);
    context.fillStyle = '#f8fbfa';
    context.fillRect(0, 0, frame.width, frame.height);
    context.strokeStyle = '#dce5e1';
    context.lineWidth = 1;
    for (const level of [0.25, 0.5, 0.75]) {
      const y = top + (bottom - top) * level;
      context.beginPath();
      context.moveTo(left, y);
      context.lineTo(right, y);
      context.stroke();
    }
    context.strokeStyle = '#0f766e';
    context.lineWidth = 2;
    context.beginPath();
    points.forEach((point, index) => {
      const x = points.length === 1 ? left : left + ((right - left) * index) / (points.length - 1);
      const y = bottom - ((point.value - min) / span) * (bottom - top);
      if (index === 0) {
        context.moveTo(x, y);
      } else {
        context.lineTo(x, y);
      }
    });
    context.stroke();
    context.fillStyle = '#17201d';
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
      render(JSON.parse(text), text.length);
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
