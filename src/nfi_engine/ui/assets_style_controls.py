from __future__ import annotations

from typing import Final

CONTROL_STYLE: Final = """
.metric, .cockpit-item, .update-state, .x7-status-item {
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 10px;
  background: var(--panel-subtle);
  min-width: 0;
}
.metric {
  background: linear-gradient(180deg, var(--panel), var(--panel-subtle));
  border-color: var(--line-strong);
}
main[data-testid="home-root"] .status-strip .metric {
  min-height: 58px;
  padding: 8px 10px;
  border-color: var(--home-line);
  border-radius: 2px;
  background:
    linear-gradient(180deg, rgb(255 255 255 / .04), rgb(255 255 255 / 0)),
    var(--home-panel-raised);
  color: var(--home-text);
  box-shadow: none;
}
.metric span, .cockpit-item span, .update-state span, .x7-status-item span {
  display: block;
  color: var(--muted);
  font-size: 12px;
  overflow-wrap: anywhere;
}
main[data-testid="home-root"] .status-strip .metric span {
  color: var(--home-muted);
  font-size: 11px;
}
.metric strong, .cockpit-item strong, .update-state strong, .x7-status-item strong {
  display: block;
  margin-top: 4px;
  font-size: 13px;
  line-height: 1.25;
  overflow-wrap: anywhere;
}
main[data-testid="home-root"] .status-strip .metric strong {
  color: var(--home-ivory);
  font-size: 18px;
  line-height: 1.15;
}
main[data-testid="home-root"] .status-strip .metric[data-testid="bot-state"] {
  border-left: 3px solid var(--home-info);
}
main[data-testid="home-root"] .status-strip .metric[data-testid="exchange-mode"] {
  border-left: 3px solid var(--home-warn);
}
main[data-testid="home-root"] .status-strip .metric[data-testid="open-trades"] {
  border-left: 3px solid var(--home-ivory);
}
main[data-testid="home-root"] .status-strip .metric[data-testid="session-pnl"] strong {
  color: var(--home-positive);
}
main[data-testid="home-root"] .status-strip .metric[data-testid="session-pnl"] {
  border-left: 3px solid var(--home-positive);
}
.settings-stack { display: grid; gap: 14px; margin-top: 18px; }
.settings-secondary-stack {
  display: grid;
  gap: 10px;
  min-width: 0;
}
.settings-focus-panel {
  border-color: var(--line-strong);
  background: linear-gradient(180deg, var(--panel), var(--panel-subtle));
}
.settings-drawer {
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
  min-width: 0;
  overflow: clip;
}
.settings-drawer[open] { border-color: var(--line-strong); }
.settings-drawer > summary {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  min-height: 40px;
  padding: 10px 12px;
  cursor: pointer;
  color: var(--ink);
  font-size: 14px;
  font-weight: 650;
}
.settings-drawer > summary::after {
  content: "+";
  color: var(--muted);
  font-family: ui-monospace, SFMono-Regular, Consolas, "Liberation Mono", monospace;
  font-size: 13px;
}
.settings-drawer[open] > summary {
  border-bottom: 1px solid var(--line);
  background: var(--panel-subtle);
}
.settings-drawer[open] > summary::after { content: "-"; }
.settings-drawer-body { padding: 12px; }
.settings-drawer-body > section {
  margin-top: 0;
  border: 0;
  border-radius: 0;
  padding: 0;
  background: transparent;
  box-shadow: none;
}
.settings-drawer .settings-stack { margin-top: 0; }
.settings-drawer .settings-group:first-child {
  border-top: 0;
  padding-top: 0;
}
.settings-drawer .settings-simple-group > h2,
.settings-drawer .settings-simple-group > .muted {
  display: none;
}
.settings-drawer .field-grid { grid-template-columns: 1fr; }
.settings-group { border-top: 1px solid var(--line); padding-top: 14px; }
.settings-group summary { cursor: pointer; font-size: 15px; font-weight: 650; }
.field-grid { display: grid; grid-template-columns: minmax(170px, .55fr) 1fr 120px; gap: 10px; }
.field-row { display: contents; }
label, .field-note, th { font-size: 13px; color: var(--muted); }
input, select, button, .button {
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: var(--panel);
  color: var(--ink);
  padding: 7px 9px;
  font: inherit;
  transition: background .2s ease, border-color .2s ease, color .2s ease, transform .12s ease;
}
input[type="checkbox"] { width: 18px; min-height: 18px; align-self: center; }
input:not([type="checkbox"]), select {
  width: 100%;
  min-width: 0;
}
button, .button {
  cursor: pointer;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
}
button:hover, .button:hover { border-color: var(--line-strong); background: var(--panel-subtle); }
button:active, .button:active { transform: translateY(1px); }
button.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: var(--panel);
}
button.primary:hover { background: var(--accent-strong); border-color: var(--accent-strong); }
button:focus-visible, input:focus-visible, select:focus-visible, a:focus-visible {
  outline: 2px solid var(--focus);
  outline-offset: 2px;
}
button:disabled, input:disabled, select:disabled {
  opacity: .62;
  cursor: not-allowed;
  transform: none;
}
.toolbar { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.setup-preview { margin-bottom: 18px; }
.setup-wizard strong { align-self: center; }
.setup-output { white-space: pre-wrap; overflow-wrap: anywhere; }
.setup-permission-drawer, .setup-credential-drawer {
  grid-column: 1 / -1;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: var(--panel-subtle);
  overflow: clip;
}
.setup-permission-drawer > summary, .setup-credential-drawer > summary {
  min-height: 36px;
  padding: 9px 10px;
  cursor: pointer;
  color: var(--ink);
  font-size: 13px;
  font-weight: 650;
}
.setup-permission-drawer[open] > summary,
.setup-credential-drawer[open] > summary {
  border-bottom: 1px solid var(--line);
}
.setup-credential-drawer .field-row {
  display: grid;
  grid-template-columns: minmax(170px, .55fr) 1fr 120px;
  gap: 10px;
  padding: 10px;
}
.setup-permission-drawer fieldset {
  display: grid;
  grid-template-columns: minmax(170px, .55fr) 1fr;
  gap: 10px;
  margin: 0;
  border: 0;
  padding: 10px;
}
.setup-permission-drawer legend {
  grid-column: 1 / -1;
  padding: 0;
  color: var(--muted);
  font-size: 12px;
}
.inline-state {
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 7px 9px;
  background: var(--panel-subtle);
  color: var(--muted);
}
.state, .audit, .lock {
  margin-top: 12px;
  border-left: 3px solid var(--accent);
  padding: 8px 10px;
  background: var(--accent-soft);
  color: var(--ink);
  min-height: 36px;
}
.lock { border-left-color: var(--warn); background: var(--warn-soft); }
main[data-testid="home-root"] .cockpit-item,
main[data-testid="home-root"] .update-state,
main[data-testid="home-root"] .x7-status-item {
  min-height: 60px;
  padding: 8px 9px;
  border-color: var(--home-line);
  border-radius: 2px;
  background:
    linear-gradient(180deg, rgb(255 255 255 / .022), transparent),
    var(--home-panel-raised);
  color: var(--home-text);
}
main[data-testid="home-root"] .cockpit-item span,
main[data-testid="home-root"] .update-state span,
main[data-testid="home-root"] .x7-status-item span {
  color: var(--home-muted);
}
main[data-testid="home-root"] .cockpit-item strong,
main[data-testid="home-root"] .update-state strong,
main[data-testid="home-root"] .x7-status-item strong {
  color: var(--home-ivory);
  font-size: 13px;
}
main[data-testid="home-root"] input,
main[data-testid="home-root"] select,
main[data-testid="home-root"] button,
main[data-testid="home-root"] .button {
  min-height: 32px;
  border-color: var(--home-line);
  border-radius: 2px;
  background: var(--home-panel-raised);
  color: var(--home-text);
  font-size: 12px;
}
main[data-testid="home-root"] button:hover,
main[data-testid="home-root"] .button:hover {
  border-color: var(--home-line-strong);
  background: var(--home-panel-hot);
}
main[data-testid="home-root"] button.primary {
  border-color: var(--home-positive);
  background: var(--home-positive);
  color: #06231a;
}
main[data-testid="home-root"] .toolbar {
  gap: 6px;
  margin-top: 8px;
}
main[data-testid="home-root"] .state,
main[data-testid="home-root"] .audit,
main[data-testid="home-root"] .lock {
  min-height: 32px;
  margin-top: 8px;
  padding: 7px 9px;
  border-left-color: var(--home-positive);
  background: var(--home-panel-raised);
  color: var(--home-text);
}
main[data-testid="home-root"] .lock {
  border-left-color: var(--home-warn);
}
"""
