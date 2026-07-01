from __future__ import annotations

from typing import Final

SHELL_STYLE: Final = """
:root {
  color-scheme: light;
  --bg: #f3f6f4;
  --bg-rail: #e7eeea;
  --panel: #ffffff;
  --panel-subtle: #f9fbfa;
  --ink: #16201c;
  --muted: #61706a;
  --line: #c8d5cf;
  --line-strong: #a9bbb2;
  --accent: #0f766e;
  --accent-strong: #0b5f59;
  --accent-soft: #dff1ed;
  --danger: #b42318;
  --danger-soft: #fff1f0;
  --warn: #9a6700;
  --warn-soft: #fff7df;
  --focus: #134e4a;
  --command: #101815;
  --command-elevated: #1b2823;
  --command-text: #f4fbf7;
  --command-muted: #a9bab2;
  --command-line: #30443d;
  --home-bg: #080d0e;
  --home-panel: #101719;
  --home-panel-raised: #162022;
  --home-panel-hot: #1c2b2e;
  --home-text: #edf7f2;
  --home-ivory: #f0ead8;
  --home-muted: #9aa9a7;
  --home-line: #2c3f43;
  --home-line-strong: #486268;
  --home-positive: #00d08a;
  --home-negative: #ff5757;
  --home-warn: #f6c44f;
  --home-info: #5ea1ff;
  --home-positive-soft: #c9ffea;
  --home-negative-soft: #ffe0e0;
  --home-warn-soft: #fff0bf;
  --shadow: 0 16px 40px rgb(22 32 28 / .08);
}
* { box-sizing: border-box; }
html { scroll-behavior: smooth; }
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
  background:
    radial-gradient(circle at 12% -8%, var(--accent-soft), transparent 26rem),
    linear-gradient(135deg, rgb(255 255 255 / .76), rgb(255 255 255 / 0) 42%),
    repeating-linear-gradient(90deg, rgb(22 32 28 / .028) 0 1px, transparent 1px 80px),
    var(--bg);
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}
main { max-width: 1180px; margin: 0 auto; padding: 24px; }
main[data-testid="home-root"] {
  padding-top: 18px;
}
header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--line);
}
main[data-testid="home-root"] > header {
  align-items: center;
  padding: 18px;
  border: 1px solid var(--command-line);
  border-radius: 8px;
  background:
    linear-gradient(135deg, rgb(255 255 255 / .07), rgb(255 255 255 / 0) 46%),
    var(--command);
  color: var(--command-text);
  box-shadow: var(--shadow);
}
main[data-testid="home-root"] > header p {
  color: var(--command-muted);
}
h1 { font-size: 24px; line-height: 1.05; margin: 0 0 6px; letter-spacing: 0; }
h2 { font-size: 15px; line-height: 1.2; margin: 0 0 12px; letter-spacing: 0; }
p { margin: 0; color: var(--muted); line-height: 1.55; text-wrap: pretty; }
a { color: var(--accent-strong); }
nav {
  display: flex;
  gap: 6px;
  padding: 4px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: var(--panel);
}
nav a {
  color: var(--ink);
  border: 1px solid transparent;
  border-radius: 5px;
  padding: 8px 11px;
  text-decoration: none;
  transition: background .2s ease, border-color .2s ease, color .2s ease;
}
nav a:hover { background: var(--panel-subtle); }
nav a[aria-current="page"] {
  border-color: var(--accent);
  background: var(--accent-soft);
  color: var(--accent-strong);
}
main[data-testid="home-root"] nav {
  border-color: var(--command-line);
  background: var(--command-elevated);
}
main[data-testid="home-root"] nav a {
  color: var(--command-text);
}
main[data-testid="home-root"] nav a:hover {
  background: rgb(255 255 255 / .08);
}
main[data-testid="home-root"] nav a[aria-current="page"] {
  border-color: var(--accent);
  background: var(--accent);
  color: var(--panel);
}
.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, .85fr);
  gap: 16px;
  margin-top: 18px;
}
.settings-workspace {
  grid-template-columns: minmax(0, 1fr) minmax(340px, .72fr);
  align-items: start;
}
.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.25fr) minmax(0, .75fr);
  gap: 16px;
  margin-top: 18px;
}
.status-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 18px;
}
main[data-testid="home-root"] .status-strip {
  gap: 10px;
  padding: 10px;
  border: 1px solid var(--command-line);
  border-radius: 8px;
  background: var(--command);
  box-shadow: var(--shadow);
}
section {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 6px;
  min-width: 0;
  padding: 16px;
  box-shadow: 0 1px 0 rgb(255 255 255 / .9) inset;
}
main[data-testid="home-root"] section {
  box-shadow: 0 1px 0 rgb(255 255 255 / .85) inset, var(--shadow);
}
section > h2 { color: var(--ink); }
.section-heading {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: start;
  margin-bottom: 14px;
}
.section-heading h2 { margin-bottom: 4px; }
.section-heading strong {
  flex: 0 0 auto;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 5px 8px;
  background: var(--panel-subtle);
  color: var(--ink);
  font-size: 12px;
  white-space: nowrap;
}
main[data-testid="home-root"] {
  width: 100%;
  max-width: none;
  min-height: 100dvh;
  margin: 0;
  padding: 7px;
  background:
    linear-gradient(90deg, rgb(94 161 255 / .12) 0 1px, transparent 1px 100%),
    repeating-linear-gradient(90deg, rgb(255 255 255 / .018) 0 1px, transparent 1px 86px),
    repeating-linear-gradient(0deg, rgb(255 255 255 / .012) 0 1px, transparent 1px 52px),
    linear-gradient(180deg, #0a1011, var(--home-bg));
  color: var(--home-text);
}
main[data-testid="home-root"] > header {
  min-height: 50px;
  align-items: center;
  padding: 7px 10px;
  border-color: var(--home-line);
  border-radius: 3px;
  background:
    linear-gradient(90deg, rgb(0 208 138 / .14), transparent 42%),
    linear-gradient(180deg, rgb(255 255 255 / .035), rgb(255 255 255 / 0)),
    var(--home-panel);
  color: var(--home-text);
  box-shadow: none;
}
main[data-testid="home-root"] > header > div {
  min-width: 0;
}
main[data-testid="home-root"] h1 {
  margin-bottom: 2px;
  color: var(--home-ivory);
  font-size: 20px;
  line-height: 1.1;
}
main[data-testid="home-root"] > header p {
  color: var(--home-muted);
  font-size: 11px;
  line-height: 1.35;
}
main[data-testid="home-root"] nav {
  flex: 0 0 auto;
  gap: 2px;
  padding: 2px;
  border-color: var(--home-line);
  border-radius: 3px;
  background: var(--home-panel-raised);
}
main[data-testid="home-root"] nav a {
  min-height: 31px;
  padding: 6px 10px;
  color: var(--home-muted);
  border-radius: 2px;
  font-size: 12px;
}
main[data-testid="home-root"] nav a:hover {
  background: var(--home-panel-hot);
  color: var(--home-text);
}
main[data-testid="home-root"] nav a[aria-current="page"] {
  border-color: var(--home-positive);
  background: var(--home-positive);
  color: #061b14;
}
main[data-testid="home-root"] .status-strip {
  gap: 5px;
  margin-top: 5px;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}
main[data-testid="home-root"] .dashboard-grid {
  grid-template-columns: minmax(0, 1.6fr) minmax(372px, .74fr);
  gap: 7px;
  margin-top: 7px;
  align-items: start;
}
main[data-testid="home-root"] section {
  padding: 9px;
  border-color: var(--home-line);
  border-radius: 3px;
  background:
    linear-gradient(180deg, rgb(255 255 255 / .022), rgb(255 255 255 / 0)),
    var(--home-panel);
  color: var(--home-text);
  box-shadow: none;
}
main[data-testid="home-root"] section > h2,
main[data-testid="home-root"] .section-heading h2 {
  margin: 0;
  color: var(--home-ivory);
  font-size: 13px;
  line-height: 1.2;
}
main[data-testid="home-root"] .section-heading {
  align-items: center;
  min-height: 34px;
  margin: -9px -9px 9px;
  padding: 7px 9px;
  border-bottom: 1px solid var(--home-line);
  background: rgb(255 255 255 / .025);
}
main[data-testid="home-root"] .section-heading p,
main[data-testid="home-root"] p,
main[data-testid="home-root"] .muted {
  color: var(--home-muted);
  font-size: 12px;
}
main[data-testid="home-root"] .section-heading strong {
  border-color: var(--home-line-strong);
  border-radius: 2px;
  background: var(--home-panel-hot);
  color: var(--home-ivory);
}
main[data-testid="home-root"] .portfolio-panel {
  grid-column: auto;
}
main[data-testid="home-root"] .home-overview {
  min-height: 402px;
  display: grid;
  grid-template-rows: auto auto 1fr;
  overflow: hidden;
  border-color: var(--home-line-strong);
  background:
    linear-gradient(135deg, rgb(0 208 138 / .055), transparent 38%),
    linear-gradient(180deg, rgb(240 234 216 / .035), transparent 32%),
    var(--home-panel);
  color: var(--home-text);
}
main[data-testid="home-root"] .home-overview::before {
  background:
    repeating-linear-gradient(90deg, rgb(255 255 255 / .026) 0 1px, transparent 1px 72px),
    repeating-linear-gradient(0deg, rgb(255 255 255 / .018) 0 1px, transparent 1px 40px);
}
main[data-testid="home-root"] .home-overview .section-heading h2,
main[data-testid="home-root"] .home-overview .overview-list h3 {
  color: var(--home-text);
}
main[data-testid="home-root"] .home-overview .section-heading p,
main[data-testid="home-root"] .home-overview .overview-list .muted {
  color: var(--home-muted);
}
main[data-testid="home-root"] .overview-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-auto-rows: minmax(82px, auto);
  gap: 5px;
}
main[data-testid="home-root"] .overview-cell {
  min-height: 82px;
  padding: 9px;
  border-color: var(--home-line);
  border-radius: 2px;
  background:
    linear-gradient(180deg, rgb(255 255 255 / .024), rgb(255 255 255 / 0)),
    var(--home-panel-raised);
  box-shadow: none;
}
main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"] {
  grid-column: span 2;
  grid-row: span 2;
  border-color: rgb(0 208 138 / .72);
  background:
    linear-gradient(135deg, rgb(0 208 138 / .16), transparent 58%),
    linear-gradient(180deg, rgb(240 234 216 / .04), transparent),
    var(--home-panel-raised);
}
main[data-testid="home-root"] .overview-cell[data-testid="overview-exposure"] {
  border-color: rgb(246 196 79 / .58);
}
main[data-testid="home-root"] .overview-cell[data-testid="overview-risk"] {
  border-color: rgb(94 161 255 / .58);
}
main[data-testid="home-root"] .overview-cell span,
main[data-testid="home-root"] .overview-cell small {
  color: var(--home-muted);
  font-size: 11px;
}
main[data-testid="home-root"] .overview-cell strong {
  color: var(--home-ivory);
  font-size: 19px;
}
main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"] strong {
  font-size: 34px;
}
main[data-testid="home-root"] .overview-cell[data-testid="overview-pnl"] strong {
  color: var(--home-positive);
}
main[data-testid="home-root"] .overview-cell[data-testid="overview-exposure"] strong {
  color: var(--home-warn);
}
main[data-testid="home-root"] .overview-split {
  align-self: stretch;
  gap: 5px;
  margin-top: 5px;
}
main[data-testid="home-root"] .overview-list {
  min-height: 100%;
  padding: 0;
  border-color: var(--home-line);
  border-radius: 2px;
  background:
    linear-gradient(180deg, rgb(255 255 255 / .022), transparent),
    var(--home-panel-raised);
  box-shadow: none;
  overflow: hidden;
}
main[data-testid="home-root"] .overview-list h3 {
  margin: 0;
  padding: 8px 9px;
  border-bottom: 1px solid var(--home-line);
  font-size: 12px;
  background: rgb(255 255 255 / .026);
}
main[data-testid="home-root"] .overview-list ul {
  gap: 0;
}
main[data-testid="home-root"] .overview-list li {
  min-height: 32px;
  grid-template-columns: minmax(0, .72fr) minmax(0, 1.1fr);
  border-top-color: var(--home-line);
  padding: 7px 9px;
}
main[data-testid="home-root"] .overview-list li:first-child {
  border-top: 0;
}
main[data-testid="home-root"] .overview-list strong,
main[data-testid="home-root"] .overview-list span {
  font-size: 11px;
}
main[data-testid="home-root"] .overview-list span {
  color: var(--home-muted);
}
main[data-testid="home-root"] .portfolio-pressure-idle {
  border-color: var(--home-line-strong);
}
main[data-testid="home-root"] .portfolio-pressure-balanced {
  border-color: var(--home-positive);
  background: rgb(24 201 147 / .12);
  color: var(--home-positive-soft);
}
main[data-testid="home-root"] .portfolio-pressure-elevated {
  border-color: var(--home-warn);
  background: rgb(255 209 102 / .13);
  color: var(--home-warn-soft);
}
main[data-testid="home-root"] .chart-panel {
  --panel-subtle: #0a1011;
  --line: var(--home-line);
  --line-strong: var(--home-line-strong);
  --accent: var(--home-positive);
  --ink: var(--home-text);
  min-height: 312px;
  gap: 8px;
  border-color: var(--home-line-strong);
  background:
    linear-gradient(180deg, rgb(94 161 255 / .05), transparent 30%),
    var(--home-panel);
}
main[data-testid="home-root"] .chart-heading,
main[data-testid="home-root"] .chart-footer {
  gap: 8px;
}
main[data-testid="home-root"] .chart-heading h2 {
  margin: 0;
  color: var(--home-ivory);
  font-size: 13px;
}
main[data-testid="home-root"] .chart-heading span,
main[data-testid="home-root"] .chart-footer .muted {
  color: var(--home-muted);
}
main[data-testid="home-root"] .chart-canvas-wrap {
  min-height: 228px;
  border-color: var(--home-line);
  border-radius: 2px;
  background:
    repeating-linear-gradient(0deg, rgb(240 234 216 / .05) 0 1px, transparent 1px 40px),
    repeating-linear-gradient(90deg, rgb(94 161 255 / .045) 0 1px, transparent 1px 56px),
    #0a1011;
  box-shadow: none;
}
main[data-testid="home-root"] .chart-canvas-wrap canvas {
  height: 240px;
}
main[data-testid="home-root"] .chart-panel .state {
  border-left-color: var(--home-info);
  background: var(--home-panel-raised);
  color: var(--home-text);
}
main[data-testid="home-root"] .chart-panel[data-chart-state="empty"] .state,
main[data-testid="home-root"] .chart-panel[data-chart-state="stale"] .state {
  border-left-color: var(--home-warn);
  background: var(--home-panel-raised);
}
main[data-testid="home-root"] .chart-panel[data-chart-state="error"] .state {
  border-left-color: var(--home-negative);
  background: var(--home-panel-raised);
}
"""
