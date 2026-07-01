from __future__ import annotations

from typing import Final

STACK_HOME_STYLE: Final = """
main[data-testid="home-root"] .status-strip {
  grid-template-columns: minmax(0, .95fr) minmax(0, 1.25fr) minmax(0, .75fr) minmax(0, 1fr);
  gap: 8px;
  margin-top: 8px;
}

main[data-testid="home-root"] .status-strip .metric {
  min-height: 68px;
  position: relative;
  padding: 10px 11px;
  border-left-width: 1px;
}

main[data-testid="home-root"] .status-strip .metric::before,
main[data-testid="home-root"] .overview-cell::before {
  position: absolute;
  inset: 0 10px auto;
  height: 2px;
  border-radius: 999px;
  background: var(--stack-info);
  content: "";
}

main[data-testid="home-root"] .status-strip .metric[data-testid="exchange-mode"]::before {
  background: var(--stack-warn);
}

main[data-testid="home-root"] .status-strip .metric[data-testid="session-pnl"]::before,
main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"]::before {
  background: var(--stack-money);
}

main[data-testid="home-root"] .status-strip .metric strong,
main[data-testid="home-root"] .overview-cell strong,
main[data-testid="home-root"] .overview-list strong,
main[data-testid="logs-root"] .machine-code,
main[data-testid="logs-root"] .log-time {
  color: var(--stack-ivory);
  font-variant-numeric: tabular-nums;
}

main[data-testid="home-root"] .dashboard-grid {
  grid-template-columns: minmax(0, 1.64fr) minmax(348px, .66fr);
  gap: 8px;
  margin-top: 8px;
}

.dashboard-primary-stack,
.dashboard-ops-rail,
main[data-testid="settings-root"] .settings-secondary-stack {
  gap: 8px;
}

main[data-testid="home-root"] .home-overview {
  min-height: 430px;
  border-color: rgb(40 224 160 / .45);
  background:
    radial-gradient(circle at 82% 6%, rgb(109 170 255 / .12), transparent 24rem),
    linear-gradient(135deg, rgb(40 224 160 / .12), transparent 46%),
    var(--stack-panel);
}

main[data-testid="home-root"] .home-overview::before {
  background:
    radial-gradient(circle at 18% 18%, rgb(40 224 160 / .08), transparent 18rem),
    linear-gradient(180deg, rgb(255 255 255 / .03), transparent);
  opacity: .75;
}

main[data-testid="home-root"] .overview-grid {
  grid-template-columns: repeat(12, minmax(0, 1fr));
  grid-auto-flow: dense;
  grid-auto-rows: minmax(88px, auto);
  gap: 8px;
}

main[data-testid="home-root"] .overview-cell {
  min-height: 88px;
  position: relative;
  padding: 12px;
  overflow: hidden;
}

main[data-testid="home-root"] .overview-cell[data-testid="overview-positions"],
main[data-testid="home-root"] .overview-cell[data-testid="overview-equity"] {
  grid-column: span 3;
}

main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"] {
  grid-column: span 5;
  grid-row: span 2;
  border-color: rgb(40 224 160 / .64);
  background:
    radial-gradient(circle at 12% 8%, rgb(40 224 160 / .20), transparent 18rem),
    var(--stack-panel-raised);
}

main[data-testid="home-root"] .overview-cell[data-testid="overview-exposure"],
main[data-testid="home-root"] .overview-cell[data-testid="overview-risk"] {
  grid-column: span 4;
}

main[data-testid="home-root"] .overview-cell[data-testid="overview-exposure"]::before {
  background: var(--stack-warn);
}

main[data-testid="home-root"] .overview-cell[data-testid="overview-risk"]::before {
  background: var(--stack-info);
}

main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"] strong {
  color: var(--stack-money);
  font-size: 42px;
}

main[data-testid="home-root"] .overview-split {
  gap: 8px;
  margin-top: 8px;
}

main[data-testid="home-root"] .overview-list h3,
main[data-testid="home-root"] .section-heading,
main[data-testid="settings-root"] .section-heading,
main[data-testid="logs-root"] section > h2 {
  border-bottom-color: var(--stack-line);
  background: rgb(255 255 255 / .028);
}

main[data-testid="home-root"] .chart-canvas-wrap {
  background:
    linear-gradient(180deg, rgb(109 170 255 / .045), transparent),
    #081113;
}

main[data-testid="home-root"] .cockpit-item,
main[data-testid="home-root"] .action-error,
main[data-testid="home-root"] .action-warning,
main[data-testid="home-root"] .action-info,
main[data-testid="home-root"] .state,
main[data-testid="home-root"] .audit,
main[data-testid="home-root"] .lock,
main[data-testid="settings-root"] .state,
main[data-testid="settings-root"] .audit,
main[data-testid="settings-root"] .lock,
.login-panel .state {
  border-left-width: 1px;
}

@media (max-width: 780px) {
  main[data-testid="home-root"] .status-strip,
  main[data-testid="home-root"] .overview-grid,
  main[data-testid="home-root"] .overview-split {
    grid-template-columns: 1fr;
  }

  main[data-testid="home-root"] .overview-cell,
  main[data-testid="home-root"] .overview-cell[data-testid="overview-positions"],
  main[data-testid="home-root"] .overview-cell[data-testid="overview-equity"],
  main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"],
  main[data-testid="home-root"] .overview-cell[data-testid="overview-exposure"],
  main[data-testid="home-root"] .overview-cell[data-testid="overview-risk"] {
    grid-column: auto;
    grid-row: auto;
  }

  main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"] strong {
    font-size: 32px;
  }
}
"""
