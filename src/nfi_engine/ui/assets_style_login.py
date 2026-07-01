from __future__ import annotations

from typing import Final

LOGIN_STYLE: Final = """
.login-shell {
  width: 100%;
  max-width: none;
  min-height: 100dvh;
  display: grid;
  place-items: center;
  padding: 18px;
  background:
    radial-gradient(circle at 26% 16%, rgb(0 208 138 / .15), transparent 18rem),
    radial-gradient(circle at 72% 84%, rgb(94 161 255 / .12), transparent 19rem),
    repeating-linear-gradient(90deg, rgb(240 234 216 / .024) 0 1px, transparent 1px 78px),
    linear-gradient(180deg, #070d0e, #101719);
}
.login-panel {
  width: min(430px, 100%);
  border-color: var(--home-line-strong);
  border-radius: 5px;
  background:
    linear-gradient(180deg, rgb(240 234 216 / .04), transparent 32%),
    var(--home-panel);
  color: var(--home-text);
}
.login-brand span {
  background: var(--home-positive);
  color: #06231a;
}
.login-panel h1 {
  color: var(--home-ivory);
}
.login-panel p,
.login-panel label {
  color: var(--home-muted);
}
.login-panel input,
.login-panel button {
  border-color: var(--home-line);
  background: var(--home-panel-raised);
  color: var(--home-text);
}
.login-panel button.primary {
  border-color: var(--home-positive);
  background: var(--home-positive);
  color: #06231a;
}
.login-panel .state {
  border-left-color: var(--home-positive);
  background: var(--home-panel-raised);
  color: var(--home-text);
}
"""
