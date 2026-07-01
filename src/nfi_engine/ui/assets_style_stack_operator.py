from __future__ import annotations

from typing import Final

STACK_OPERATOR_STYLE: Final = """
main[data-testid="home-root"] button,
main[data-testid="home-root"] .button,
main[data-testid="settings-root"] button,
main[data-testid="settings-root"] .button,
main[data-testid="logs-root"] button,
main[data-testid="logs-root"] .button,
main[data-testid="logs-root"] .log-tools a,
.login-panel button,
.settings-drawer > summary {
  transition:
    background var(--stack-ease),
    border-color var(--stack-ease),
    color var(--stack-ease),
    transform var(--stack-ease);
}

main[data-testid="home-root"] section,
main[data-testid="settings-root"] section,
main[data-testid="logs-root"] section,
main[data-testid="settings-root"] .settings-drawer,
main[data-testid="home-root"] .metric,
main[data-testid="home-root"] .overview-cell,
main[data-testid="home-root"] .overview-list,
main[data-testid="home-root"] .cockpit-item,
main[data-testid="home-root"] .update-state,
main[data-testid="home-root"] .x7-status-item,
main[data-testid="home-root"] .signal-list li,
main[data-testid="logs-root"] tbody tr {
  transition:
    background var(--stack-ease),
    border-color var(--stack-ease),
    box-shadow var(--stack-ease),
    transform var(--stack-ease);
}

main[data-testid="home-root"] button:hover,
main[data-testid="home-root"] .button:hover,
main[data-testid="settings-root"] button:hover,
main[data-testid="settings-root"] .button:hover,
main[data-testid="logs-root"] button:hover,
main[data-testid="logs-root"] .button:hover,
main[data-testid="logs-root"] .log-tools a:hover,
.login-panel button:hover,
.settings-drawer > summary:hover {
  transform: translateY(-1px);
}

main[data-testid="home-root"] button:active,
main[data-testid="home-root"] .button:active,
main[data-testid="settings-root"] button:active,
main[data-testid="settings-root"] .button:active,
main[data-testid="logs-root"] button:active,
main[data-testid="logs-root"] .button:active,
.login-panel button:active {
  transform: translateY(0);
}

main[data-testid="home-root"] section:hover,
main[data-testid="home-root"] .metric:hover,
main[data-testid="home-root"] .overview-cell:hover,
main[data-testid="home-root"] .cockpit-item:hover,
main[data-testid="home-root"] .update-state:hover,
main[data-testid="home-root"] .x7-status-item:hover,
main[data-testid="home-root"] .signal-list li:hover,
main[data-testid="settings-root"] .settings-drawer:hover,
main[data-testid="logs-root"] tbody tr:hover {
  border-color: var(--stack-line-strong);
  background:
    linear-gradient(180deg, rgb(255 255 255 / .062), rgb(255 255 255 / .016)),
    var(--stack-panel-raised);
}

main[data-testid="home-root"] .overview-cell:hover,
main[data-testid="home-root"] .metric:hover,
main[data-testid="home-root"] .cockpit-item:hover {
  transform: translateY(-1px);
  box-shadow: var(--stack-inset), 0 12px 28px rgb(0 0 0 / .18);
}

main[data-testid="home-root"] .cockpit-item[data-testid="cockpit-latest-error"],
main[data-testid="home-root"] .cockpit-item[data-testid="cockpit-next-action"] {
  grid-template-columns: minmax(0, .68fr) minmax(0, 1.32fr);
}

main[data-testid="home-root"] .cockpit-item[data-testid="cockpit-latest-error"] strong {
  font-size: 13px;
  line-height: 1.15;
}

main[data-testid="home-root"] section:focus-within,
main[data-testid="settings-root"] section:focus-within,
main[data-testid="settings-root"] .settings-drawer:focus-within,
main[data-testid="logs-root"] section:focus-within,
.login-panel:focus-within {
  border-color: rgb(40 224 160 / .78);
  box-shadow: var(--stack-inset), 0 0 0 3px rgb(40 224 160 / .10);
}

main[data-testid="settings-root"] input:focus-visible,
main[data-testid="settings-root"] select:focus-visible,
main[data-testid="settings-root"] button:focus-visible,
main[data-testid="logs-root"] input:focus-visible,
main[data-testid="logs-root"] select:focus-visible,
main[data-testid="logs-root"] button:focus-visible,
main[data-testid="home-root"] button:focus-visible,
.login-panel input:focus-visible,
.login-panel button:focus-visible,
nav a:focus-visible,
.settings-drawer > summary:focus-visible {
  outline: 2px solid rgb(40 224 160 / .78);
  outline-offset: 2px;
}

main[data-testid="settings-root"] .settings-workspace {
  grid-template-columns: minmax(0, 1.22fr) minmax(340px, .58fr);
  gap: 10px;
}

main[data-testid="settings-root"] .settings-focus-panel {
  border-color: rgb(40 224 160 / .46);
  background:
    radial-gradient(circle at 8% 0, rgb(40 224 160 / .12), transparent 24rem),
    var(--stack-panel);
}

main[data-testid="settings-root"] .settings-drawer > summary {
  min-height: 44px;
  background: rgb(255 255 255 / .026);
}

main[data-testid="settings-root"] .setup-permission-drawer,
main[data-testid="settings-root"] .setup-credential-drawer,
main[data-testid="settings-root"] .inline-state {
  border-color: var(--stack-line);
  background: var(--stack-panel-raised);
  color: var(--stack-text);
}

main[data-testid="settings-root"] .setup-permission-drawer > summary,
main[data-testid="settings-root"] .setup-credential-drawer > summary {
  color: var(--stack-text);
  background: rgb(255 255 255 / .026);
  transition:
    background var(--stack-ease),
    color var(--stack-ease);
}

main[data-testid="settings-root"] .setup-permission-drawer > summary:hover,
main[data-testid="settings-root"] .setup-credential-drawer > summary:hover {
  color: var(--stack-money);
  background: var(--stack-panel-hot);
}

main[data-testid="settings-root"] .setup-permission-drawer[open] > summary,
main[data-testid="settings-root"] .setup-credential-drawer[open] > summary {
  border-bottom-color: var(--stack-line);
  color: var(--stack-money);
}

main[data-testid="settings-root"] .setup-permission-drawer legend,
main[data-testid="settings-root"] .field-note {
  color: var(--stack-muted);
}

main[data-testid="settings-root"] .settings-drawer[open] > summary {
  color: var(--stack-money);
}

main[data-testid="settings-root"] .settings-drawer > summary::after {
  transition: transform var(--stack-ease);
}

main[data-testid="settings-root"] .settings-drawer[open] > summary::after {
  transform: rotate(180deg);
}

main[data-testid="logs-root"] tbody tr:nth-child(even) td {
  background: rgb(255 255 255 / .012);
}

main[data-testid="home-root"] .cockpit-item strong,
main[data-testid="home-root"] section[data-testid="recent-errors"] strong,
main[data-testid="logs-root"] .machine-code,
main[data-testid="logs-root"] td {
  overflow-wrap: anywhere;
}

main[data-testid="logs-root"] th {
  background: var(--stack-panel-raised);
}

main[data-testid="logs-root"] td {
  background: rgb(255 255 255 / .006);
}

@media (max-width: 1180px) {
  main[data-testid="home-root"] .dashboard-grid,
  main[data-testid="settings-root"] .settings-workspace {
    grid-template-columns: 1fr;
  }
}

@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    scroll-behavior: auto;
    transition-duration: .01ms;
  }

  main[data-testid="home-root"] nav a:hover,
  main[data-testid="home-root"] button:hover,
  main[data-testid="home-root"] .overview-cell:hover,
  main[data-testid="home-root"] .metric:hover,
  main[data-testid="home-root"] .cockpit-item:hover,
  main[data-testid="settings-root"] button:hover,
  main[data-testid="logs-root"] button:hover,
  .settings-drawer > summary:hover {
    transform: none;
  }
}
"""
