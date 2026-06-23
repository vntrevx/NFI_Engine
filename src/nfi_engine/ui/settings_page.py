from __future__ import annotations

from html import escape

from nfi_engine.config import RuntimeSettings
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey
from nfi_engine.ui.pairlist import render_pairlist_panel
from nfi_engine.ui.readiness import render_readiness_panel
from nfi_engine.ui.runtime_controls import render_runtime_controls
from nfi_engine.ui.settings_data_lifecycle import render_settings_data_lifecycle_panel
from nfi_engine.ui.settings_fields import render_settings_fields
from nfi_engine.ui.settings_update import render_settings_update_panel
from nfi_engine.ui.setup_wizard import render_setup_wizard


def render_settings_body(
    *,
    settings: RuntimeSettings,
    nav: str,
    readiness: PreflightReport | None = None,
) -> str:
    locale = settings.ui.locale
    rows = render_settings_fields(settings)
    setup_panel = render_setup_wizard(settings, locale=locale)
    update_panel = render_settings_update_panel(settings=settings)
    readiness_panel = render_readiness_panel(readiness, locale=locale)
    runtime_controls = render_runtime_controls(settings=settings, locale=locale)
    pairlist_panel = render_pairlist_panel(settings, read_only=settings.ui.read_only)
    lifecycle_panel = render_settings_data_lifecycle_panel(settings=settings)
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
    {update_panel}
    {readiness_panel}
    {runtime_controls}
    {pairlist_panel}
    {lifecycle_panel}
    <section>
      <h2>{localize(locale, MessageKey.SETTINGS_SAFETY_GATES)}</h2>
      <div class="lock" data-testid="live-trading-locked">
        {localize(locale, MessageKey.SETTINGS_LIVE_LOCKED)}
      </div>
      <div class="toolbar">
        <button data-testid="restore-button"{disabled} type="button">
          {localize(locale, MessageKey.RESTORE)}
        </button>
      </div>
    </section>
  </div>
</main>
"""


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
