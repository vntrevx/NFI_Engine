from __future__ import annotations

from typing import Final

OPERATOR_STYLE: Final = """
main[data-testid="settings-root"],
main[data-testid="logs-root"] {
  width: 100%;
  max-width: none;
  min-height: 100dvh;
  margin: 0;
  padding: 8px;
  background:
    repeating-linear-gradient(90deg, rgb(94 161 255 / .045) 0 1px, transparent 1px 88px),
    repeating-linear-gradient(0deg, rgb(240 234 216 / .018) 0 1px, transparent 1px 52px),
    linear-gradient(180deg, #081010, #0d1517);
  color: var(--home-text);
}
main[data-testid="settings-root"] > header,
main[data-testid="logs-root"] > header {
  min-height: 56px;
  align-items: center;
  padding: 12px 14px;
  border: 1px solid var(--home-line);
  border-radius: 4px;
  background:
    linear-gradient(90deg, rgb(0 208 138 / .12), transparent 38%),
    linear-gradient(180deg, rgb(240 234 216 / .035), transparent),
    var(--home-panel);
  color: var(--home-text);
}
main[data-testid="settings-root"] h1,
main[data-testid="logs-root"] h1 {
  color: var(--home-ivory);
  font-size: 21px;
}
main[data-testid="settings-root"] h2,
main[data-testid="logs-root"] h2,
main[data-testid="settings-root"] .settings-group summary {
  color: var(--home-ivory);
}
main[data-testid="settings-root"] p,
main[data-testid="logs-root"] p,
main[data-testid="settings-root"] label,
main[data-testid="logs-root"] label,
main[data-testid="settings-root"] .field-note,
main[data-testid="logs-root"] th,
main[data-testid="settings-root"] .muted,
main[data-testid="logs-root"] .muted {
  color: var(--home-muted);
}
main[data-testid="settings-root"] > header p,
main[data-testid="logs-root"] > header p {
  color: var(--home-muted);
}
main[data-testid="settings-root"] nav,
main[data-testid="logs-root"] nav {
  border-color: var(--home-line);
  background: var(--home-panel-raised);
}
main[data-testid="settings-root"] nav a,
main[data-testid="logs-root"] nav a {
  min-height: 32px;
  color: var(--home-muted);
  border-radius: 3px;
}
main[data-testid="settings-root"] nav a:hover,
main[data-testid="logs-root"] nav a:hover {
  background: var(--home-panel-hot);
  color: var(--home-text);
}
main[data-testid="settings-root"] nav a[aria-current="page"],
main[data-testid="logs-root"] nav a[aria-current="page"] {
  border-color: var(--home-positive);
  background: var(--home-positive);
  color: #06231a;
}
main[data-testid="settings-root"] .workspace,
main[data-testid="logs-root"] .workspace {
  gap: 8px;
  margin-top: 8px;
}
main[data-testid="settings-root"] .settings-workspace {
  grid-template-columns: minmax(0, 1.04fr) minmax(360px, .58fr);
}
main[data-testid="settings-root"] section,
main[data-testid="logs-root"] section,
main[data-testid="settings-root"] .settings-drawer {
  border-color: var(--home-line);
  border-radius: 4px;
  background:
    linear-gradient(180deg, rgb(240 234 216 / .032), transparent 30%),
    var(--home-panel);
  color: var(--home-text);
  box-shadow: none;
}
main[data-testid="settings-root"] .settings-focus-panel {
  min-height: calc(100dvh - 88px);
  border-color: rgb(0 208 138 / .58);
  background:
    radial-gradient(circle at 8% 0, rgb(0 208 138 / .12), transparent 21rem),
    linear-gradient(180deg, rgb(240 234 216 / .04), transparent 28%),
    var(--home-panel);
}
main[data-testid="settings-root"] .section-heading,
main[data-testid="logs-root"] section > h2 {
  margin: -16px -16px 14px;
  padding: 11px 14px;
  border-bottom: 1px solid var(--home-line);
  background: rgb(240 234 216 / .026);
}
main[data-testid="logs-root"] section > h2 {
  margin-bottom: 12px;
}
main[data-testid="settings-root"] .settings-secondary-stack {
  gap: 8px;
}
main[data-testid="settings-root"] .settings-drawer {
  overflow: hidden;
}
main[data-testid="settings-root"] .settings-drawer[open] {
  border-color: var(--home-line-strong);
}
main[data-testid="settings-root"] .settings-drawer > summary {
  min-height: 42px;
  color: var(--home-ivory);
  background: rgb(240 234 216 / .018);
}
main[data-testid="settings-root"] .settings-drawer > summary::after {
  color: var(--home-positive);
}
main[data-testid="settings-root"] .settings-drawer[open] > summary {
  border-bottom-color: var(--home-line);
  background: var(--home-panel-raised);
}
main[data-testid="settings-root"] .settings-drawer-body {
  padding: 12px;
}
main[data-testid="settings-root"] .settings-group,
main[data-testid="settings-root"] .setup-permission-drawer,
main[data-testid="settings-root"] .setup-credential-drawer {
  border-color: var(--home-line);
}
main[data-testid="settings-root"] input,
main[data-testid="settings-root"] select,
main[data-testid="settings-root"] button,
main[data-testid="settings-root"] .button,
main[data-testid="logs-root"] input,
main[data-testid="logs-root"] select,
main[data-testid="logs-root"] button,
main[data-testid="logs-root"] .button,
main[data-testid="logs-root"] .log-tools a {
  border-color: var(--home-line);
  background: var(--home-panel-raised);
  color: var(--home-text);
}
main[data-testid="settings-root"] button:hover,
main[data-testid="settings-root"] .button:hover,
main[data-testid="logs-root"] button:hover,
main[data-testid="logs-root"] .button:hover,
main[data-testid="logs-root"] .log-tools a:hover {
  border-color: var(--home-line-strong);
  background: var(--home-panel-hot);
}
main[data-testid="settings-root"] button.primary,
main[data-testid="logs-root"] button.primary {
  border-color: var(--home-positive);
  background: var(--home-positive);
  color: #06231a;
}
main[data-testid="settings-root"] .state,
main[data-testid="settings-root"] .audit,
main[data-testid="settings-root"] .lock,
main[data-testid="logs-root"] .state,
main[data-testid="logs-root"] .audit,
main[data-testid="logs-root"] .lock {
  border-left-color: var(--home-positive);
  background: var(--home-panel-raised);
  color: var(--home-text);
}
main[data-testid="settings-root"] .lock,
main[data-testid="logs-root"] .lock {
  border-left-color: var(--home-warn);
}
main[data-testid="logs-root"] .log-tools {
  gap: 8px;
}
main[data-testid="logs-root"] .log-tools label {
  display: grid;
  gap: 5px;
}
main[data-testid="logs-root"] .log-tools a {
  min-height: 36px;
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--home-line);
  border-radius: 5px;
  padding: 7px 9px;
  text-decoration: none;
  white-space: nowrap;
}
main[data-testid="logs-root"] .table-scroll {
  border-color: var(--home-line);
  border-radius: 3px;
  background: #080d0e;
}
main[data-testid="logs-root"] table {
  color: var(--home-text);
}
main[data-testid="logs-root"] th {
  background: var(--home-panel-raised);
  border-bottom-color: var(--home-line);
}
main[data-testid="logs-root"] td {
  border-top-color: var(--home-line);
}
main[data-testid="logs-root"] .machine-code,
main[data-testid="logs-root"] .log-time {
  color: var(--home-ivory);
}
main[data-testid="logs-root"] .severity-error {
  color: var(--home-negative);
}
@media (max-width: 900px) {
  main[data-testid="settings-root"] .settings-workspace,
  main[data-testid="logs-root"] .workspace {
    grid-template-columns: 1fr;
  }
  main[data-testid="settings-root"] .settings-focus-panel {
    min-height: auto;
  }
}
@media (max-width: 720px) {
  main[data-testid="settings-root"],
  main[data-testid="logs-root"] {
    padding: 6px;
  }
  main[data-testid="settings-root"] > header,
  main[data-testid="logs-root"] > header {
    align-items: stretch;
  }
}
"""
