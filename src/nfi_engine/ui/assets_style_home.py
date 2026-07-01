from __future__ import annotations

from typing import Final

HOME_STYLE: Final = """
main[data-testid="home-root"] {
  --home-gutter: 8px;
  background:
    linear-gradient(90deg, rgb(94 161 255 / .10) 0 1px, transparent 1px 92px),
    repeating-linear-gradient(0deg, rgb(240 234 216 / .014) 0 1px, transparent 1px 46px),
    linear-gradient(180deg, #090f10, var(--home-bg));
}
main[data-testid="home-root"] > header,
main[data-testid="home-root"] .metric,
main[data-testid="home-root"] section,
main[data-testid="home-root"] .overview-cell,
main[data-testid="home-root"] .overview-list,
main[data-testid="home-root"] .signal-list li {
  box-shadow: 0 1px 0 rgb(240 234 216 / .06) inset;
}
main[data-testid="home-root"] > header {
  min-height: 56px;
  border-color: var(--home-line-strong);
  background:
    linear-gradient(90deg, rgb(0 208 138 / .16), transparent 34%),
    linear-gradient(180deg, rgb(240 234 216 / .045), transparent),
    var(--home-panel);
}
main[data-testid="home-root"] .status-strip {
  grid-template-columns: 1.2fr 1.1fr .8fr 1.1fr;
}
main[data-testid="home-root"] .status-strip .metric {
  min-height: 64px;
  display: grid;
  align-content: space-between;
  border-top: 1px solid var(--home-line-strong);
}
main[data-testid="home-root"] .dashboard-grid {
  grid-template-columns: minmax(0, 1fr) minmax(348px, 25vw);
  gap: var(--home-gutter);
}
.dashboard-primary-stack,
.dashboard-ops-rail {
  min-width: 0;
  display: grid;
  gap: var(--home-gutter);
  align-content: start;
}
.dashboard-ops-rail {
  position: sticky;
  top: 8px;
}
main[data-testid="home-root"] .home-overview {
  min-height: 418px;
  border-color: rgb(0 208 138 / .48);
  background:
    radial-gradient(circle at 12% 10%, rgb(0 208 138 / .16), transparent 20rem),
    radial-gradient(circle at 92% 0, rgb(94 161 255 / .12), transparent 18rem),
    linear-gradient(180deg, rgb(240 234 216 / .04), transparent 38%),
    var(--home-panel);
}
main[data-testid="home-root"] .overview-grid {
  grid-template-columns: minmax(0, 1.12fr) minmax(0, 1.12fr) minmax(0, .9fr);
  grid-auto-rows: minmax(94px, auto);
  gap: var(--home-gutter);
}
main[data-testid="home-root"] .overview-cell {
  min-height: 94px;
  padding: 10px;
}
main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"] {
  grid-column: span 2;
  grid-row: span 2;
}
main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"] strong {
  font-size: clamp(30px, 4.2vw, 48px);
  line-height: .95;
}
main[data-testid="home-root"] .overview-cell[data-testid="overview-equity"],
main[data-testid="home-root"] .overview-cell[data-testid="overview-risk"] {
  border-color: rgb(94 161 255 / .46);
}
main[data-testid="home-root"] .overview-split {
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: var(--home-gutter);
}
main[data-testid="home-root"] .overview-list li {
  min-height: 36px;
  grid-template-columns: minmax(0, .62fr) minmax(0, 1.18fr);
}
main[data-testid="home-root"] .chart-panel {
  min-height: 292px;
}
main[data-testid="home-root"] .chart-canvas-wrap {
  min-height: 210px;
}
main[data-testid="home-root"] .chart-canvas-wrap canvas {
  height: 220px;
}
main[data-testid="home-root"] .cockpit-grid {
  grid-template-columns: 1fr;
}
main[data-testid="home-root"] .cockpit-item {
  min-height: 52px;
  display: grid;
  grid-template-columns: minmax(0, .85fr) minmax(0, 1.05fr);
  gap: 8px;
  align-items: center;
}
main[data-testid="home-root"] .cockpit-item span {
  margin: 0;
}
main[data-testid="home-root"] .cockpit-item strong {
  margin: 0;
  text-align: right;
}
main[data-testid="home-root"] section[data-testid="runtime-controls"] .toolbar {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
main[data-testid="home-root"] .x7-status-grid,
main[data-testid="home-root"] .execution-safety .signal-list {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
main[data-testid="home-root"] .action-error,
main[data-testid="home-root"] .action-warning,
main[data-testid="home-root"] .action-info {
  grid-template-columns: minmax(0, 1fr);
}
main[data-testid="home-root"] .action-error a,
main[data-testid="home-root"] .action-warning a,
main[data-testid="home-root"] .action-info a {
  grid-column: 1;
  grid-row: auto;
  justify-self: start;
}
@media (max-width: 1180px) {
  main[data-testid="home-root"] .dashboard-grid {
    grid-template-columns: 1fr;
  }
  .dashboard-ops-rail {
    position: static;
  }
}
@media (max-width: 780px) {
  main[data-testid="home-root"] .status-strip,
  main[data-testid="home-root"] .overview-grid,
  main[data-testid="home-root"] .overview-split,
  main[data-testid="home-root"] .x7-status-grid,
  main[data-testid="home-root"] .execution-safety .signal-list {
    grid-template-columns: 1fr;
  }
  main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"] {
    grid-column: auto;
  }
  main[data-testid="home-root"] .cockpit-item {
    grid-template-columns: 1fr;
  }
  main[data-testid="home-root"] .cockpit-item strong {
    text-align: left;
  }
}
"""
