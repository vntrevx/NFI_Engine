from __future__ import annotations

from html import escape
from typing import assert_never

from nfi_engine.config import Locale, RuntimeSettings
from nfi_engine.exchange import (
    ExchangeCapabilityProfile,
    ExchangeSupportLevel,
    get_official_requirement,
    list_exchange_profiles,
)
from nfi_engine.exchange.capabilities import normalize_exchange_id
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_exchange_select(*, common: str, value: str, locale: Locale, disabled: str = "") -> str:
    options = _exchange_options(value=value, locale=locale)
    return f'<select {common}{disabled} data-exchange-select="true">{options}</select>'


def render_setup_exchange_select(
    *,
    field_id: str,
    name: str,
    value: str,
    locale: Locale,
) -> str:
    options = _exchange_options(value=value, locale=locale)
    escaped_id = escape(field_id)
    escaped_name = escape(name)
    return (
        f'<select id="{escaped_id}" name="{escaped_name}" '
        f'data-exchange-select="true">{options}</select>'
    )


def render_exchange_registry_panel(*, settings: RuntimeSettings, locale: Locale) -> str:
    profiles = list_exchange_profiles()
    active_id = normalize_exchange_id(settings.exchange.name)
    options = "\n".join(
        _exchange_option_button(profile=profile, active_id=active_id, locale=locale)
        for profile in profiles
    )
    verified = sum(
        1 for profile in profiles if profile.support_level is ExchangeSupportLevel.VERIFIED
    )
    official_required = _official_requirement_profiles(profiles)
    official_checked = sum(
        1
        for profile in official_required
        if get_official_requirement(profile.exchange_id) is not None
    )
    verified_label = localize(locale, MessageKey.SETTINGS_EXCHANGE_SUPPORT_VERIFIED)
    official_label = localize(locale, MessageKey.SETTINGS_EXCHANGE_OFFICIAL_CHECKED)
    count_text = (
        f"{verified}/{len(profiles)} {verified_label} | "
        f"{official_checked}/{len(official_required)} {official_label}"
    )
    return f"""
    <section class="exchange-registry" data-testid="exchange-registry-panel">
      <div class="section-heading">
        <div>
          <h2>{localize(locale, MessageKey.SETTINGS_EXCHANGE_REGISTRY_TITLE)}</h2>
          <p>{localize(locale, MessageKey.SETTINGS_EXCHANGE_REGISTRY_HELP)}</p>
        </div>
        <strong data-testid="exchange-registry-count">{escape(count_text)}</strong>
      </div>
      <div class="exchange-option-list">
{options}
      </div>
    </section>
"""


def _exchange_options(*, value: str, locale: Locale) -> str:
    profiles = list_exchange_profiles()
    current_id = normalize_exchange_id(value)
    profile_ids = frozenset(profile.exchange_id for profile in profiles)
    options = [
        _exchange_option(profile=profile, current_id=current_id, locale=locale)
        for profile in profiles
    ]
    if value.strip() and current_id not in profile_ids:
        options.append(_unknown_current_option(value=value, locale=locale))
    return "\n".join(options)


def _official_requirement_profiles(
    profiles: tuple[ExchangeCapabilityProfile, ...],
) -> tuple[ExchangeCapabilityProfile, ...]:
    return tuple(
        profile
        for profile in profiles
        if profile.support_level in (ExchangeSupportLevel.VERIFIED, ExchangeSupportLevel.CANDIDATE)
    )


def _exchange_option(
    *,
    profile: ExchangeCapabilityProfile,
    current_id: str,
    locale: Locale,
) -> str:
    selected = " selected" if current_id == profile.exchange_id else ""
    label = " - ".join(
        (
            profile.display_name,
            _support_label(profile.support_level, locale=locale),
            _mode_label(profile, locale=locale),
        )
    )
    return f'<option value="{escape(profile.exchange_id)}"{selected}>{escape(label)}</option>'


def _unknown_current_option(*, value: str, locale: Locale) -> str:
    selected = " selected"
    label = localize(locale, MessageKey.SETTINGS_EXCHANGE_UNKNOWN_CURRENT).format(exchange=value)
    return f'<option value="{escape(value)}"{selected}>{escape(label)}</option>'


def _exchange_option_button(
    *,
    profile: ExchangeCapabilityProfile,
    active_id: str,
    locale: Locale,
) -> str:
    active_class = " is-active" if active_id == profile.exchange_id else ""
    mode = _default_mode(profile)
    support = _support_label(profile.support_level, locale=locale)
    support_class = escape(profile.support_level.value)
    support_label = escape(support)
    capability_pills = "".join(_capability_pills(profile=profile, locale=locale))
    official_summary = _official_summary(profile=profile, locale=locale)
    return f"""
        <button
          type="button"
          class="exchange-option{active_class}"
          data-exchange-pick="{escape(profile.exchange_id)}"
          data-exchange-mode="{escape(mode)}"
          data-testid="exchange-option-{escape(profile.exchange_id)}"
        >
          <span class="exchange-option-head">
            <strong>{escape(profile.display_name)}</strong>
            <span class="support-badge support-{support_class}">{support_label}</span>
          </span>
          <span class="capability-pills">{capability_pills}</span>
          {official_summary}
          <span class="exchange-evidence">
            {escape(profile.checked_on.isoformat())} - {escape(profile.evidence)}
          </span>
        </button>
"""


def _capability_pills(
    *,
    profile: ExchangeCapabilityProfile,
    locale: Locale,
) -> tuple[str, ...]:
    pills: list[str] = []
    if profile.supports_spot:
        pills.append(_pill(localize(locale, MessageKey.SETTINGS_EXCHANGE_MODE_SPOT)))
    if profile.supports_futures:
        pills.append(_pill(localize(locale, MessageKey.SETTINGS_EXCHANGE_MODE_FUTURES)))
    if profile.supports_testnet:
        pills.append(_pill(localize(locale, MessageKey.SETTINGS_EXCHANGE_CAP_TESTNET)))
    if profile.supports_sandbox:
        pills.append(_pill(localize(locale, MessageKey.SETTINGS_EXCHANGE_CAP_SANDBOX)))
    if profile.supports_market_orders:
        pills.append(_pill(localize(locale, MessageKey.SETTINGS_EXCHANGE_CAP_MARKET)))
    if profile.supports_data_only:
        pills.append(_pill(localize(locale, MessageKey.SETTINGS_EXCHANGE_CAP_DATA_ONLY)))
    return tuple(pills)


def _pill(label: str) -> str:
    return f"<span>{escape(label)}</span>"


def _official_summary(*, profile: ExchangeCapabilityProfile, locale: Locale) -> str:
    requirement = get_official_requirement(profile.exchange_id)
    if requirement is None:
        return ""
    checked_label = localize(locale, MessageKey.SETTINGS_EXCHANGE_OFFICIAL_CHECKED)
    credential_label = localize(locale, MessageKey.SETTINGS_EXCHANGE_OFFICIAL_CREDENTIALS)
    credentials = ", ".join(requirement.credential_fields)
    return (
        '<span class="exchange-official">'
        f"{escape(checked_label)} {escape(requirement.checked_on.isoformat())} - "
        f"{escape(credential_label)}: {escape(credentials)}"
        "</span>"
    )


def _mode_label(profile: ExchangeCapabilityProfile, *, locale: Locale) -> str:
    modes: list[str] = []
    if profile.supports_spot:
        modes.append(localize(locale, MessageKey.SETTINGS_EXCHANGE_MODE_SPOT))
    if profile.supports_futures:
        modes.append(localize(locale, MessageKey.SETTINGS_EXCHANGE_MODE_FUTURES))
    if not modes:
        return localize(locale, MessageKey.SETTINGS_EXCHANGE_CAP_DATA_ONLY)
    return "/".join(modes)


def _default_mode(profile: ExchangeCapabilityProfile) -> str:
    if profile.supports_futures:
        return "futures"
    if profile.supports_spot:
        return "spot"
    return ""


def _support_label(level: ExchangeSupportLevel, *, locale: Locale) -> str:
    match level:
        case ExchangeSupportLevel.VERIFIED:
            return localize(locale, MessageKey.SETTINGS_EXCHANGE_SUPPORT_VERIFIED)
        case ExchangeSupportLevel.CANDIDATE:
            return localize(locale, MessageKey.SETTINGS_EXCHANGE_SUPPORT_CANDIDATE)
        case ExchangeSupportLevel.GENERIC_UNVERIFIED:
            return localize(locale, MessageKey.SETTINGS_EXCHANGE_SUPPORT_GENERIC)
        case unreachable:
            assert_never(unreachable)
