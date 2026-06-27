from __future__ import annotations

from html import escape

from nfi_engine.config import RuntimeSettings
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_login_body(*, settings: RuntimeSettings) -> str:
    locale = settings.ui.locale
    username = escape(settings.api.operator_username)
    return f"""
<main data-testid="login-root" class="login-shell">
  <section class="login-panel">
    <div class="login-brand">
      <span>NFI</span>
      <strong>Engine</strong>
    </div>
    <h1>NFI Engine</h1>
    <p>{localize(locale, MessageKey.LOGIN_SUBTITLE)}</p>
    <form data-testid="login-form" class="login-form">
      <label for="operator-username">
        {localize(locale, MessageKey.LOGIN_USERNAME_LABEL)}
      </label>
      <input
        id="operator-username"
        name="username"
        type="text"
        value="{username}"
        autocomplete="username"
        data-testid="login-username"
      >
      <label for="operator-password">
        {localize(locale, MessageKey.LOGIN_CREDENTIAL_LABEL)}
      </label>
      <input
        id="operator-password"
        name="password"
        type="password"
        autocomplete="current-password"
        data-testid="login-password"
      >
      <button type="submit" class="primary" data-testid="login-button">
        {localize(locale, MessageKey.LOGIN_UNLOCK)}
      </button>
    </form>
    <div class="state" data-testid="login-state">
      {localize(locale, MessageKey.LOGIN_ACCOUNT_HINT)}
    </div>
  </section>
</main>
"""
