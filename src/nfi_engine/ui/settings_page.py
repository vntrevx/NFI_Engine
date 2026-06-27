from __future__ import annotations

from html import escape
from typing import Final, assert_never

from nfi_engine.config import Locale, RiskProfileName, RuntimeSettings
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey
from nfi_engine.ui.pairlist import render_pairlist_panel
from nfi_engine.ui.readiness import render_readiness_panel
from nfi_engine.ui.runtime_controls import render_runtime_controls
from nfi_engine.ui.settings_data_lifecycle import render_settings_data_lifecycle_panel
from nfi_engine.ui.settings_exchange import render_exchange_registry_panel
from nfi_engine.ui.settings_fields import render_settings_fields
from nfi_engine.ui.settings_update import render_settings_update_panel
from nfi_engine.ui.setup_wizard import render_setup_wizard

SETTINGS_FORM_ID: Final = "settings-form"
RISK_PROFILE_OPTIONS: Final = (
    RiskProfileName.SAFE,
    RiskProfileName.BALANCED,
    RiskProfileName.EXPERT,
)


def render_settings_body(
    *,
    settings: RuntimeSettings,
    nav: str,
    readiness: PreflightReport | None = None,
) -> str:
    locale = settings.ui.locale
    advanced_label = localize(locale, MessageKey.SETTINGS_ADVANCED)
    rows = render_settings_fields(settings)
    setup_panel = render_setup_wizard(settings, locale=locale)
    exchange_panel = render_exchange_registry_panel(settings=settings, locale=locale)
    update_panel = render_settings_update_panel(settings=settings)
    readiness_panel = render_readiness_panel(readiness, locale=locale)
    runtime_controls = render_runtime_controls(settings=settings, locale=locale)
    pairlist_panel = render_pairlist_panel(settings, read_only=settings.ui.read_only)
    lifecycle_panel = render_settings_data_lifecycle_panel(settings=settings)
    readonly_panel = _readonly_panel(settings)
    settings_editor = _settings_editor(settings=settings, rows=rows)
    safety_panel = _safety_panel(settings)
    exchange_drawer = _drawer(
        test_id="exchange-registry-drawer",
        title=localize(locale, MessageKey.SETTINGS_EXCHANGE_REGISTRY_TITLE),
        content=exchange_panel,
    )
    readiness_drawer = _drawer(
        test_id="readiness-drawer",
        title=localize(locale, MessageKey.READINESS_TITLE),
        content=readiness_panel,
    )
    runtime_drawer = _drawer(
        test_id="runtime-controls-drawer",
        title=localize(locale, MessageKey.SETTINGS_RUNTIME_CONTROL_STATE),
        content=runtime_controls,
    )
    pairlist_drawer = _drawer(
        test_id="pairlist-drawer",
        title=localize(locale, MessageKey.PAIRLIST_TITLE),
        content=pairlist_panel,
    )
    lifecycle_drawer = _drawer(
        test_id="data-lifecycle-drawer",
        title=localize(locale, MessageKey.SETTINGS_DATA_LIFECYCLE_TITLE),
        content=lifecycle_panel,
    )
    update_drawer = _drawer(
        test_id="settings-update-drawer",
        title=localize(locale, MessageKey.SETTINGS_UPDATE_TITLE),
        content=update_panel,
    )
    return f"""
<main data-testid="settings-root">
  <header>
    <div>
      <h1>NFI Engine</h1>
      <p>{localize(locale, MessageKey.SETTINGS_TITLE)}</p>
    </div>
    {nav}
  </header>
  <div class="workspace settings-workspace">
    <section class="settings-primary-panel settings-focus-panel">
      <div class="section-heading">
        <div>
          <h2>{localize(locale, MessageKey.SETTINGS_RUNTIME_SAFE_TITLE)}</h2>
          <p>{localize(locale, MessageKey.SETTINGS_SIMPLE_HELP)}</p>
        </div>
      </div>
      {setup_panel}
    </section>
    <aside class="settings-secondary-stack" aria-label="{advanced_label}">
      {readonly_panel}
      {settings_editor}
      {exchange_drawer}
      {readiness_drawer}
      {runtime_drawer}
      {pairlist_drawer}
      {lifecycle_drawer}
      {update_drawer}
      {safety_panel}
    </aside>
  </div>
</main>
"""


def _settings_editor(*, settings: RuntimeSettings, rows: str) -> str:
    locale = settings.ui.locale
    disabled = _disabled_attrs(settings)
    content = f"""
      <form id="{SETTINGS_FORM_ID}" data-testid="settings-form" class="settings-stack">{rows}</form>
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
"""
    return _open_drawer(
        test_id="settings-edit-drawer",
        title=localize(locale, MessageKey.SETTINGS_SIMPLE_MODE),
        content=content,
    )


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


def _safety_panel(settings: RuntimeSettings) -> str:
    locale = settings.ui.locale
    disabled = _disabled_attrs(settings)
    content = f"""
      <div class="settings-risk-limits" data-testid="settings-risk-limit-controls">
        {_risk_profile_control(settings)}
        {_expert_confirmation_control(settings)}
      </div>
      <div class="lock" data-testid="live-trading-locked">
        {localize(locale, MessageKey.SETTINGS_LIVE_LOCKED)}
      </div>
      <div class="toolbar">
        <button data-testid="restore-button"{disabled} type="button">
          {localize(locale, MessageKey.RESTORE)}
        </button>
      </div>
"""
    return _drawer(
        test_id="settings-safety-drawer",
        title=localize(locale, MessageKey.SETTINGS_SAFETY_GATES),
        content=content,
    )


def _risk_profile_control(settings: RuntimeSettings) -> str:
    locale = settings.ui.locale
    disabled = _disabled_attrs(settings)
    options = "\n".join(
        _risk_profile_option(
            option=option,
            current=settings.risk.risk_profile,
            locale=locale,
        )
        for option in RISK_PROFILE_OPTIONS
    )
    label = localize(locale, MessageKey.FIELD_RISK_PROFILE)
    return f"""
        <div class="field-row" data-testid="settings-risk-profile-control">
          <label for="settings-risk-profile">{label}</label>
          <select id="settings-risk-profile" form="{SETTINGS_FORM_ID}"
            name="risk.risk_profile" data-testid="field-risk.risk_profile"
            data-runtime-safe="true"{disabled}>
{options}
          </select>
          <span class="field-note">{localize(locale, MessageKey.SETTINGS_RUNTIME_SAFE)}</span>
        </div>
"""


def _risk_profile_option(
    *,
    option: RiskProfileName,
    current: RiskProfileName,
    locale: Locale,
) -> str:
    selected = " selected" if current is option else ""
    label_key = _risk_profile_label(option)
    label = localize(locale, label_key)
    return f'<option value="{escape(option.value)}"{selected}>{label}</option>'


def _risk_profile_label(option: RiskProfileName) -> MessageKey:
    match option:
        case RiskProfileName.SAFE:
            return MessageKey.SETUP_OPTION_SAFE
        case RiskProfileName.BALANCED:
            return MessageKey.SETUP_OPTION_BALANCED
        case RiskProfileName.EXPERT:
            return MessageKey.SETUP_OPTION_EXPERT
        case unreachable:
            assert_never(unreachable)


def _expert_confirmation_control(settings: RuntimeSettings) -> str:
    locale = settings.ui.locale
    disabled = _disabled_attrs(settings)
    checked = " checked" if settings.risk.expert_risk_confirmed else ""
    return f"""
        <label class="inline-check" for="settings-expert-risk-confirmed">
          <input id="settings-expert-risk-confirmed" form="{SETTINGS_FORM_ID}"
            name="risk.expert_risk_confirmed" data-testid="field-risk.expert_risk_confirmed"
            data-runtime-safe="true" type="checkbox"{checked}{disabled}>
          {localize(locale, MessageKey.FIELD_EXPERT_RISK_CONFIRMED)}
        </label>
"""


def _open_drawer(*, test_id: str, title: str, content: str) -> str:
    return f"""
    <details class="settings-drawer" open data-testid="{escape(test_id)}">
      <summary>{escape(title)}</summary>
      <div class="settings-drawer-body">
{content}
      </div>
    </details>
"""


def _drawer(*, test_id: str, title: str, content: str) -> str:
    return f"""
    <details class="settings-drawer" data-testid="{escape(test_id)}">
      <summary>{escape(title)}</summary>
      <div class="settings-drawer-body">
{content}
      </div>
    </details>
"""


def _disabled_attrs(settings: RuntimeSettings) -> str:
    if not settings.ui.read_only:
        return ""
    title = escape(localize(settings.ui.locale, MessageKey.SETTINGS_READONLY_DISABLED_TITLE))
    return f' disabled title="{title}"'
