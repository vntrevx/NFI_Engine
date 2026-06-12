from __future__ import annotations

from nfi_engine.config import RuntimeSettings
from nfi_engine.ui.i18n import format_message, localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_login_body(*, settings: RuntimeSettings) -> str:
    locale = settings.ui.locale
    return f"""
<main data-testid="login-root" class="login-shell">
  <section class="login-panel">
    <h1>NFI Engine</h1>
    <p>{localize(locale, MessageKey.LOGIN_SUBTITLE)}</p>
    <form data-testid="login-form" class="login-form">
      <label for="operator-token">{localize(locale, MessageKey.LOGIN_TOKEN_LABEL)}</label>
      <input
        id="operator-token"
        name="token"
        type="password"
        autocomplete="off"
        data-testid="login-token"
      >
      <button type="submit" class="primary" data-testid="login-button">
        {localize(locale, MessageKey.LOGIN_UNLOCK)}
      </button>
    </form>
    <div class="state" data-testid="login-state">
      {localize(locale, MessageKey.LOGIN_TOKEN_HELP)}
    </div>
    <p class="muted">
      {
        format_message(
            locale,
            MessageKey.LOGIN_TOKEN_FILE,
            host=settings.api.host,
            port=settings.api.port,
        )
    }
    </p>
  </section>
</main>
"""
