from __future__ import annotations

from typing import Final

STACK_BASE_STYLE: Final = """
:root {
  --stack-canvas: #060b0c;
  --stack-panel: #0d1517;
  --stack-panel-raised: #121d20;
  --stack-panel-hot: #19272a;
  --stack-line: #263a3e;
  --stack-line-strong: #3e5a60;
  --stack-text: #eef7f4;
  --stack-muted: #91a5a2;
  --stack-money: #28e0a0;
  --stack-info: #6daaff;
  --stack-warn: #f5c65d;
  --stack-ivory: #f1ead8;
  --stack-radius: 6px;
  --stack-radius-tight: 4px;
  --stack-shadow: 0 18px 48px rgb(0 0 0 / .24);
  --stack-inset: 0 1px 0 rgb(255 255 255 / .055) inset;
  --stack-ease: 150ms ease;
}

body {
  background:
    radial-gradient(circle at 18% -18%, rgb(40 224 160 / .13), transparent 31rem),
    radial-gradient(circle at 90% 4%, rgb(109 170 255 / .10), transparent 29rem),
    linear-gradient(180deg, #071011, var(--stack-canvas));
}

main[data-testid="home-root"],
main[data-testid="settings-root"],
main[data-testid="logs-root"],
.login-shell {
  color: var(--stack-text);
  background:
    radial-gradient(circle at 9% 0, rgb(40 224 160 / .11), transparent 26rem),
    radial-gradient(circle at 94% 6%, rgb(109 170 255 / .09), transparent 26rem),
    linear-gradient(180deg, #071011, var(--stack-canvas));
}

main[data-testid="home-root"] > header,
main[data-testid="settings-root"] > header,
main[data-testid="logs-root"] > header,
.login-panel {
  border-color: var(--stack-line-strong);
  border-radius: var(--stack-radius);
  background:
    linear-gradient(135deg, rgb(40 224 160 / .10), transparent 38%),
    linear-gradient(180deg, rgb(255 255 255 / .05), transparent 42%),
    var(--stack-panel);
  box-shadow: var(--stack-inset), var(--stack-shadow);
}

main[data-testid="home-root"] h1,
main[data-testid="settings-root"] h1,
main[data-testid="logs-root"] h1,
.login-panel h1 {
  color: var(--stack-ivory);
  font-size: 21px;
}

main[data-testid="home-root"] > header p,
main[data-testid="settings-root"] > header p,
main[data-testid="logs-root"] > header p,
.login-panel p {
  color: var(--stack-muted);
}

main[data-testid="home-root"] nav,
main[data-testid="settings-root"] nav,
main[data-testid="logs-root"] nav {
  border-color: var(--stack-line);
  border-radius: var(--stack-radius-tight);
  background: rgb(255 255 255 / .035);
}

main[data-testid="home-root"] nav a,
main[data-testid="settings-root"] nav a,
main[data-testid="logs-root"] nav a {
  min-height: 32px;
  border-radius: 3px;
  color: var(--stack-muted);
  transition:
    background var(--stack-ease),
    border-color var(--stack-ease),
    color var(--stack-ease),
    transform var(--stack-ease);
}

main[data-testid="home-root"] nav a:hover,
main[data-testid="settings-root"] nav a:hover,
main[data-testid="logs-root"] nav a:hover {
  background: var(--stack-panel-hot);
  color: var(--stack-text);
  transform: translateY(-1px);
}

main[data-testid="home-root"] nav a[aria-current="page"],
main[data-testid="settings-root"] nav a[aria-current="page"],
main[data-testid="logs-root"] nav a[aria-current="page"] {
  border-color: rgb(40 224 160 / .72);
  background: rgb(40 224 160 / .16);
  color: var(--stack-money);
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
main[data-testid="home-root"] .state,
main[data-testid="home-root"] .audit,
main[data-testid="home-root"] .lock,
main[data-testid="logs-root"] .table-scroll {
  border: 1px solid var(--stack-line);
  border-radius: var(--stack-radius);
  background:
    linear-gradient(180deg, rgb(255 255 255 / .045), rgb(255 255 255 / .012)),
    var(--stack-panel);
  box-shadow: var(--stack-inset);
}
"""
