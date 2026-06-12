from __future__ import annotations

from html import escape
from typing import Final

from nfi_engine.config import Locale, RuntimeSettings
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey
from nfi_engine.ui.pairlist import render_pairlist_panel
from nfi_engine.ui.readiness import render_readiness_panel
from nfi_engine.ui.settings_fields import render_settings_fields

SETUP_OPTION_LABELS: Final[dict[str, MessageKey]] = {
    "aggressive": MessageKey.SETUP_OPTION_AGGRESSIVE,
    "balanced": MessageKey.SETUP_OPTION_BALANCED,
    "conservative": MessageKey.SETUP_OPTION_CONSERVATIVE,
    "futures": MessageKey.SETUP_OPTION_FUTURES,
    "live": MessageKey.SETUP_OPTION_LIVE,
    "paper": MessageKey.SETUP_OPTION_PAPER,
    "spot": MessageKey.SETUP_OPTION_SPOT,
    "testnet": MessageKey.SETUP_OPTION_TESTNET,
}


def render_settings_body(
    *,
    settings: RuntimeSettings,
    nav: str,
    readiness: PreflightReport | None = None,
) -> str:
    locale = settings.ui.locale
    rows = render_settings_fields(settings)
    setup_panel = _setup_preview_panel(settings, locale=locale)
    readiness_panel = render_readiness_panel(readiness, locale=locale)
    pairlist_panel = render_pairlist_panel(settings, read_only=settings.ui.read_only)
    readonly_panel = _readonly_panel(settings)
    disabled = _disabled_attrs(settings)
    return f"""
<main data-testid="settings-root">
  <header>
    <div>
      <h1>NFI Engine</h1>
      <p>{localize(locale, MessageKey.SETTINGS_TITLE)}</p>
    </div>
    {nav}
  </header>
  <div class="workspace">
    <section>
      <h2>{localize(locale, MessageKey.SETTINGS_RUNTIME_SAFE_TITLE)}</h2>
      {setup_panel}
      <form data-testid="settings-form" class="settings-stack">{rows}</form>
      <div class="toolbar">
        <button type="button" data-testid="validate-button">
          {localize(locale, MessageKey.VALIDATE)}
        </button>
        <button data-testid="save-draft-button"{disabled} type="button">
          {localize(locale, MessageKey.SAVE_DRAFT)}
        </button>
        <button data-testid="apply-button"{disabled} type="button" class="primary">
          {localize(locale, MessageKey.APPLY)}
        </button>
      </div>
      <div class="state" data-testid="validation-state">
        {localize(locale, MessageKey.SETTINGS_NO_VALIDATION)}
      </div>
      <div class="state" data-testid="draft-state">
        {localize(locale, MessageKey.SETTINGS_NO_DRAFT)}
      </div>
      <div class="audit" data-testid="audit-log">
        {localize(locale, MessageKey.SETTINGS_NO_AUDIT)}
      </div>
    </section>
    {readonly_panel}
    {readiness_panel}
    {pairlist_panel}
    <section>
      <h2>{localize(locale, MessageKey.SETTINGS_SAFETY_GATES)}</h2>
      <div class="lock" data-testid="live-trading-locked">
        {localize(locale, MessageKey.SETTINGS_LIVE_LOCKED)}
      </div>
      <div class="toolbar">
        <button data-testid="restore-button"{disabled} type="button">
          {localize(locale, MessageKey.RESTORE)}
        </button>
        <button data-testid="start-button"{disabled} type="button">
          {localize(locale, MessageKey.START)}
        </button>
        <button data-testid="stop-button"{disabled} type="button">
          {localize(locale, MessageKey.STOP)}
        </button>
      </div>
    </section>
  </div>
</main>
"""


def _setup_preview_panel(settings: RuntimeSettings, *, locale: Locale) -> str:
    intent = "testnet" if settings.exchange.testnet else "live"
    return f"""
      <div data-testid="setup-preview-panel" class="setup-preview">
        <h2>{localize(locale, MessageKey.SETUP_TITLE)}</h2>
        <form data-testid="setup-form" class="field-grid">
          <label for="setup-exchange">{localize(locale, MessageKey.SETUP_EXCHANGE)}</label>
          <input id="setup-exchange" name="exchange" value="{escape(settings.exchange.name)}">
          <span class="field-note">{localize(locale, MessageKey.SETTINGS_RELOAD_REQUIRED)}</span>
          <label for="setup-trading-mode">{localize(locale, MessageKey.SETUP_MARKET_MODE)}</label>
          <select id="setup-trading-mode" name="trading_mode">
            {_option(locale=locale, value=settings.exchange.trading_mode.value, option="spot")}
            {_option(locale=locale, value=settings.exchange.trading_mode.value, option="futures")}
          </select>
          <span class="field-note">{localize(locale, MessageKey.SETTINGS_RELOAD_REQUIRED)}</span>
          <label for="setup-intent">{localize(locale, MessageKey.SETUP_INTENT)}</label>
          <select id="setup-intent" name="intent">
            {_option(locale=locale, value=intent, option="paper")}
            {_option(locale=locale, value=intent, option="testnet")}
            {_option(locale=locale, value=intent, option="live")}
          </select>
          <span class="field-note">{localize(locale, MessageKey.SETUP_SAFETY_GATED)}</span>
          <label for="setup-risk-preset">{localize(locale, MessageKey.SETUP_RISK_PRESET)}</label>
          <select id="setup-risk-preset" name="risk_preset">
            {_option(locale=locale, value="balanced", option="conservative")}
            {_option(locale=locale, value="balanced", option="balanced")}
            {_option(locale=locale, value="balanced", option="aggressive")}
          </select>
          <span class="field-note">{localize(locale, MessageKey.SETUP_PREVIEW_ONLY)}</span>
          <label for="setup-api-key">{localize(locale, MessageKey.SETUP_API_KEY)}</label>
          <input id="setup-api-key" name="api_key" type="password" autocomplete="off">
          <span class="field-note">{localize(locale, MessageKey.SETUP_WRITE_ONLY)}</span>
          <label for="setup-api-secret">{localize(locale, MessageKey.SETUP_API_SECRET)}</label>
          <input id="setup-api-secret" name="api_secret" type="password" autocomplete="off">
          <span class="field-note">{localize(locale, MessageKey.SETUP_WRITE_ONLY)}</span>
        </form>
        <div class="toolbar">
          <button type="button" data-testid="setup-preview-button">
            {localize(locale, MessageKey.SETUP_PREVIEW_SETUP)}
          </button>
        </div>
        <pre class="state setup-output" data-testid="setup-preview-state">\
{localize(locale, MessageKey.SETUP_NO_PREVIEW)}</pre>
      </div>
"""


def _option(*, locale: Locale, value: str, option: str) -> str:
    selected = " selected" if value == option else ""
    label = localize(locale, SETUP_OPTION_LABELS[option])
    return f'<option value="{escape(option)}"{selected}>{escape(label)}</option>'


def _readonly_panel(settings: RuntimeSettings) -> str:
    if not settings.ui.read_only:
        return ""
    locale = settings.ui.locale
    return f"""
    <section data-testid="readonly-panel">
      <h2>{localize(locale, MessageKey.SETTINGS_READONLY_ACCESS)}</h2>
      <div class="lock" data-testid="readonly-reason">
        {localize(locale, MessageKey.SETTINGS_READONLY_REASON)}
      </div>
    </section>
"""


def _disabled_attrs(settings: RuntimeSettings) -> str:
    if not settings.ui.read_only:
        return ""
    title = escape(localize(settings.ui.locale, MessageKey.SETTINGS_READONLY_DISABLED_TITLE))
    return f' disabled title="{title}"'
