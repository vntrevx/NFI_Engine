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
    linear-gradient(135deg, rgb(255 255 255 / .72), rgb(255 255 255 / 0) 36%),
    repeating-linear-gradient(90deg, rgb(22 32 28 / .025) 0 1px, transparent 1px 80px),
    var(--bg);
  color: var(--ink);
  font-variant-numeric: tabular-nums;
}
main { max-width: 1180px; margin: 0 auto; padding: 24px; }
header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 18px;
  border-bottom: 1px solid var(--line);
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
section {
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 6px;
  min-width: 0;
  padding: 16px;
  box-shadow: 0 1px 0 rgb(255 255 255 / .9) inset;
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
"""
