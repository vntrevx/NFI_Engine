from __future__ import annotations

from typing import Final

STYLE: Final = """
:root {
  color-scheme: light;
  --bg: #f5f7f6;
  --panel: #ffffff;
  --ink: #17201d;
  --muted: #5b6863;
  --line: #ccd6d1;
  --accent: #0f766e;
  --danger: #b42318;
  --warn: #9a6700;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  font-family:
    Aptos,
    "Segoe UI",
    "Noto Sans CJK KR",
    "Noto Sans KR",
    "Apple SD Gothic Neo",
    "Malgun Gothic",
    ui-sans-serif,
    system-ui,
    sans-serif;
  background: var(--bg);
  color: var(--ink);
}
main { max-width: 1160px; margin: 0 auto; padding: 24px; }
header { display: flex; align-items: end; justify-content: space-between; gap: 16px; }
h1 { font-size: 24px; margin: 0 0 4px; letter-spacing: 0; }
p { margin: 0; color: var(--muted); }
nav { display: flex; gap: 8px; }
nav a {
  color: var(--ink);
  border: 1px solid var(--line);
  padding: 8px 12px;
  text-decoration: none;
  background: var(--panel);
}
nav a[aria-current="page"] { border-color: var(--accent); color: var(--accent); }
.workspace {
  display: grid;
  grid-template-columns: 1.15fr .85fr;
  gap: 18px;
  margin-top: 20px;
}
.dashboard-grid {
  display: grid;
  grid-template-columns: 1.25fr .75fr;
  gap: 18px;
  margin-top: 18px;
}
.status-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin-top: 18px;
}
.metric {
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 12px;
  background: #fff;
  min-width: 0;
}
.metric span { display: block; color: var(--muted); font-size: 12px; }
.metric strong { display: block; margin-top: 5px; overflow-wrap: anywhere; }
section {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 6px;
  padding: 16px;
}
h2 { font-size: 15px; margin: 0 0 12px; letter-spacing: 0; }
.settings-stack { display: grid; gap: 14px; margin-top: 18px; }
.settings-group { border-top: 1px solid var(--line); padding-top: 14px; }
.settings-group summary { cursor: pointer; font-size: 15px; font-weight: 700; }
.field-grid { display: grid; grid-template-columns: minmax(170px, .55fr) 1fr 120px; gap: 10px; }
.field-row { display: contents; }
label, .field-note, th { font-size: 13px; color: var(--muted); }
input, select, button {
  min-height: 36px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #fff;
  color: var(--ink);
  padding: 7px 9px;
  font: inherit;
}
input[type="checkbox"] { width: 18px; min-height: 18px; align-self: center; }
button { cursor: pointer; }
button.primary { background: var(--accent); border-color: var(--accent); color: #fff; }
button:disabled, input:disabled, select:disabled { opacity: .62; cursor: not-allowed; }
.toolbar { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.setup-preview { margin-bottom: 18px; }
.setup-output { white-space: pre-wrap; overflow-wrap: anywhere; }
.state, .audit, .lock {
  margin-top: 12px;
  border-left: 3px solid var(--accent);
  padding: 8px 10px;
  background: #eef8f6;
  color: var(--ink);
  min-height: 36px;
}
.lock { border-left-color: var(--warn); background: #fff8e1; }
.log-tools { display: flex; flex-wrap: wrap; gap: 8px; align-items: end; }
.log-tools input { min-width: 260px; max-width: 100%; }
.table-scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; }
table { width: 100%; border-collapse: collapse; margin-top: 12px; table-layout: fixed; }
.table-scroll table { margin-top: 0; }
th, td { border-bottom: 1px solid var(--line); padding: 9px 7px; text-align: left; }
td { font-size: 13px; overflow-wrap: anywhere; }
.logs-table { min-width: 680px; }
.logs-table th:nth-child(1), .logs-table td:nth-child(1) { width: 132px; }
.logs-table th:nth-child(2), .logs-table td:nth-child(2) { width: 72px; }
.logs-table th:nth-child(3), .logs-table td:nth-child(3) { width: 158px; }
.logs-table th:nth-child(4), .logs-table td:nth-child(4) { width: 180px; }
.severity-error { color: var(--danger); font-weight: 700; }
.detail { min-height: 92px; white-space: pre-line; }
@media (max-width: 780px) {
  main { padding: 16px; }
  header, .workspace { display: block; }
  .dashboard-grid, .status-strip { grid-template-columns: 1fr; }
  nav { margin-top: 12px; }
  section { margin-top: 14px; }
  .field-grid { grid-template-columns: 1fr; }
}
"""
