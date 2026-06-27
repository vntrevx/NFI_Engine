from __future__ import annotations

from typing import Final

OPERATIONS_STYLE: Final = """
.cockpit { grid-column: span 1; }
.cockpit-grid, .update-state-grid, .x7-status-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.cockpit-item[data-testid="cockpit-latest-error"] { grid-column: 1 / -1; }
.action-error, .action-warning, .action-info {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 3px 10px;
  align-items: start;
  padding: 9px 0;
  border-bottom: 1px solid var(--line);
}
.action-error:last-child, .action-warning:last-child, .action-info:last-child {
  border-bottom: 0;
}
.action-error strong, .action-warning strong, .action-info strong {
  font-size: 13px;
  grid-column: 1;
}
.action-error span, .action-warning span, .action-info span {
  color: var(--muted);
  font-size: 12px;
  grid-column: 1;
  overflow-wrap: anywhere;
}
.action-error a, .action-warning a, .action-info a {
  grid-column: 2;
  grid-row: 1 / span 2;
  color: var(--accent);
  font-size: 12px;
  text-decoration: none;
}
.action-error { border-left: 3px solid var(--danger); padding-left: 8px; }
.action-warning { border-left: 3px solid var(--warn); padding-left: 8px; }
.action-info { border-left: 3px solid var(--accent); padding-left: 8px; }
.x7-status { grid-column: 1 / -1; }
.x7-status-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); margin-top: 12px; }
.log-tools { display: flex; flex-wrap: wrap; gap: 8px; align-items: end; }
.log-tools input { min-width: 260px; max-width: 100%; }
.table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { width: 100%; border-collapse: collapse; margin-top: 12px; table-layout: fixed; }
.table-scroll table { margin-top: 0; }
th, td { border-bottom: 1px solid var(--line); padding: 9px 7px; text-align: left; }
th { background: var(--panel-subtle); font-weight: 650; }
td { font-size: 13px; overflow-wrap: anywhere; }
.logs-table { min-width: 760px; }
.logs-table th:nth-child(1), .logs-table td:nth-child(1) { width: 150px; }
.logs-table th:nth-child(2), .logs-table td:nth-child(2) { width: 72px; }
.logs-table th:nth-child(3), .logs-table td:nth-child(3) { width: 190px; }
.logs-table th:nth-child(4), .logs-table td:nth-child(4) { width: 180px; }
.log-time,
.machine-code {
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
  font-size: 12px;
  white-space: nowrap;
  word-break: keep-all;
  overflow-wrap: normal;
}
.severity-error { color: var(--danger); font-weight: 700; }
.detail { min-height: 92px; white-space: pre-line; }
.login-shell {
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 24px;
}
.login-panel {
  width: min(100%, 430px);
  padding: 28px;
  border: 1px solid var(--line-strong);
  border-radius: 6px;
  background: linear-gradient(180deg, var(--panel), var(--panel-subtle));
  box-shadow: var(--shadow);
}
.login-brand {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  min-height: 30px;
  margin-bottom: 18px;
  padding: 3px 8px 3px 3px;
  border: 1px solid var(--line);
  background: var(--panel);
}
.login-brand span {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  background: var(--ink);
  color: var(--panel);
  font-size: 11px;
  font-weight: 700;
}
.login-brand strong { font-size: 12px; }
.login-form { display: grid; gap: 9px; margin-top: 18px; }
.login-form button { justify-content: center; margin-top: 4px; }
@media (max-width: 780px) {
  main { padding: 16px; }
  header, .workspace { display: block; }
  .dashboard-grid, .status-strip { grid-template-columns: 1fr; }
  header { padding-bottom: 14px; }
  nav { margin-top: 12px; overflow-x: auto; }
  section { margin-top: 14px; }
  .settings-secondary-stack { margin-top: 14px; }
  .settings-drawer-body > section { margin-top: 0; }
  .section-heading, .exchange-option-head { display: grid; }
  .field-grid { grid-template-columns: 1fr; }
  .setup-permission-drawer fieldset { grid-template-columns: 1fr; }
  .setup-credential-drawer .field-row { grid-template-columns: 1fr; }
  .cockpit-grid, .update-state-grid, .x7-status-grid { grid-template-columns: 1fr; }
  .logs-table th:nth-child(2), .logs-table td:nth-child(2) { width: 72px; }
  .logs-table th:nth-child(3), .logs-table td:nth-child(3) { width: 190px; }
  .action-error, .action-warning, .action-info { grid-template-columns: 1fr; }
  .action-error a, .action-warning a, .action-info a {
    grid-column: 1;
    grid-row: auto;
  }
}
"""
