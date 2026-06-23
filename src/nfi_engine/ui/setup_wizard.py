from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import Final

from nfi_engine.config import Locale, RuntimeSettings
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey
from nfi_engine.ui.setup_secret import render_secret_step
from nfi_engine.ui.setup_wallet import render_wallet_step

RECOMMENDED_LEVERAGE: Final = "3x"
SETUP_OPTION_LABELS: Final[dict[str, MessageKey]] = {
    "aggressive": MessageKey.SETUP_OPTION_AGGRESSIVE,
    "balanced": MessageKey.SETUP_OPTION_BALANCED,
    "conservative": MessageKey.SETUP_OPTION_CONSERVATIVE,
    "disabled": MessageKey.SETUP_OPTION_DISABLED,
    "enabled": MessageKey.SETUP_OPTION_ENABLED,
    "expert": MessageKey.SETUP_OPTION_EXPERT,
    "futures": MessageKey.SETUP_OPTION_FUTURES,
    "live": MessageKey.SETUP_OPTION_LIVE,
    "not_applicable": MessageKey.SETUP_OPTION_NOT_APPLICABLE,
    "paper": MessageKey.SETUP_OPTION_PAPER,
    "safe": MessageKey.SETUP_OPTION_SAFE,
    "spot": MessageKey.SETUP_OPTION_SPOT,
    "testnet": MessageKey.SETUP_OPTION_TESTNET,
    "unknown": MessageKey.SETUP_OPTION_UNKNOWN,
}
PERMISSION_OPTIONS: Final = ("unknown", "enabled", "disabled", "not_applicable")


def render_setup_wizard(settings: RuntimeSettings, *, locale: Locale) -> str:
    intent = "live" if settings.engine.live_trading else "paper"
    amount = _decimal(settings.risk.stake_usdt)
    steps = "\n".join(
        (
            _exchange_step(settings, locale=locale),
            render_secret_step(
                test_id="setup-step-api-key",
                label=localize(locale, MessageKey.SETUP_API_KEY),
                field_id="setup-api-key",
                name="api_key",
                locale=locale,
            ),
            render_secret_step(
                test_id="setup-step-api-secret",
                label=localize(locale, MessageKey.SETUP_API_SECRET),
                field_id="setup-api-secret",
                name="api_secret",
                locale=locale,
            ),
            _permission_step(settings, locale=locale),
            _leverage_step(locale=locale),
            _risk_profile_step(settings, locale=locale),
            render_wallet_step(locale=locale),
            _amount_step(amount, locale=locale),
            _market_mode_step(settings, locale=locale),
            _intent_step(intent, locale=locale),
        )
    )
    return f"""
      <div data-testid="setup-preview-panel" class="setup-preview">
        <h2>{localize(locale, MessageKey.SETUP_TITLE)}</h2>
        <form data-testid="setup-form" class="setup-wizard field-grid">
{steps}
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


def _risk_profile_step(settings: RuntimeSettings, *, locale: Locale) -> str:
    label = localize(locale, MessageKey.SETUP_RISK_PROFILE)
    return f"""
          <div class="field-row" data-testid="setup-step-risk-profile">
            <label for="setup-risk-profile">{label}</label>
            <select id="setup-risk-profile" name="risk_profile">
              {_option(locale=locale, value=settings.risk.risk_profile.value, option="safe")}
              {_option(locale=locale, value=settings.risk.risk_profile.value, option="balanced")}
              {_option(locale=locale, value=settings.risk.risk_profile.value, option="expert")}
            </select>
            <label class="inline-check" for="setup-expert-risk-confirmed">
              <input id="setup-expert-risk-confirmed" name="expert_risk_confirmed"
                type="checkbox" value="true">
              {localize(locale, MessageKey.SETUP_RISK_EXPERT_CONFIRM)}
            </label>
          </div>
"""


def _permission_step(settings: RuntimeSettings, *, locale: Locale) -> str:
    return f"""
          <fieldset class="field-row" data-testid="setup-step-permission-audit">
            <legend>{localize(locale, MessageKey.SETUP_PERMISSION_AUDIT)}</legend>
            {
        _permission_select(
            locale=locale,
            field_id="setup-permission-read",
            name="permission_read",
            label=MessageKey.SETUP_PERMISSION_READ,
            value=settings.exchange.permission_read.value,
        )
    }
            {
        _permission_select(
            locale=locale,
            field_id="setup-permission-trade",
            name="permission_trade",
            label=MessageKey.SETUP_PERMISSION_TRADE,
            value=settings.exchange.permission_trade.value,
        )
    }
            {
        _permission_select(
            locale=locale,
            field_id="setup-permission-futures",
            name="permission_futures",
            label=MessageKey.SETUP_PERMISSION_FUTURES,
            value=settings.exchange.permission_futures.value,
        )
    }
            {
        _permission_select(
            locale=locale,
            field_id="setup-permission-withdrawal",
            name="permission_withdrawal",
            label=MessageKey.SETUP_PERMISSION_WITHDRAWAL,
            value=settings.exchange.permission_withdrawal.value,
        )
    }
            {
        _permission_select(
            locale=locale,
            field_id="setup-permission-ip-allowlist",
            name="permission_ip_allowlist",
            label=MessageKey.SETUP_PERMISSION_IP_ALLOWLIST,
            value=settings.exchange.permission_ip_allowlist.value,
        )
    }
          </fieldset>
"""


def _permission_select(
    *,
    locale: Locale,
    field_id: str,
    name: str,
    label: MessageKey,
    value: str,
) -> str:
    options = "\n".join(
        _option(locale=locale, value=value, option=option) for option in PERMISSION_OPTIONS
    )
    return (
        f'<label for="{field_id}">{localize(locale, label)}</label>'
        f'<select id="{field_id}" name="{name}">{options}</select>'
    )


def _leverage_step(*, locale: Locale) -> str:
    return f"""
          <div class="field-row" data-testid="setup-step-leverage">
            <label for="setup-recommended-leverage">\
{localize(locale, MessageKey.SETUP_RECOMMENDED_LEVERAGE)}</label>
            <strong id="setup-recommended-leverage" data-testid="setup-recommended-leverage">\
{RECOMMENDED_LEVERAGE}</strong>
            <span class="field-note">{localize(locale, MessageKey.SETUP_SAFETY_GATED)}</span>
          </div>
"""


def _amount_step(amount: str, *, locale: Locale) -> str:
    return f"""
          <div class="field-row" data-testid="setup-step-allocated-amount">
            <label for="setup-allocated-amount">\
{localize(locale, MessageKey.SETUP_ALLOCATED_AMOUNT)}</label>
            <input id="setup-allocated-amount" name="allocated_amount_usdt"
              type="number" min="1" step="0.01" value="{escape(amount)}">
            <span class="field-note">{localize(locale, MessageKey.SETUP_PREVIEW_ONLY)}</span>
          </div>
"""


def _market_mode_step(settings: RuntimeSettings, *, locale: Locale) -> str:
    value = settings.exchange.trading_mode.value
    return f"""
          <div class="field-row" data-testid="setup-step-market-mode">
            <label for="setup-trading-mode">{localize(locale, MessageKey.SETUP_MARKET_MODE)}</label>
            <select id="setup-trading-mode" name="trading_mode">
              {_option(locale=locale, value=value, option="spot")}
              {_option(locale=locale, value=value, option="futures")}
            </select>
            <span class="field-note">{localize(locale, MessageKey.SETTINGS_RELOAD_REQUIRED)}</span>
          </div>
"""


def _intent_step(intent: str, *, locale: Locale) -> str:
    return f"""
          <div class="field-row" data-testid="setup-step-intent">
            <label for="setup-intent">{localize(locale, MessageKey.SETUP_INTENT)}</label>
            <select id="setup-intent" name="intent">
              {_option(locale=locale, value=intent, option="paper")}
              {_option(locale=locale, value=intent, option="testnet")}
              {_option(locale=locale, value=intent, option="live")}
            </select>
            <span class="field-note">{localize(locale, MessageKey.SETUP_LIVE_WARNING)}</span>
          </div>
"""


def _exchange_step(settings: RuntimeSettings, *, locale: Locale) -> str:
    return f"""
          <div class="field-row" data-testid="setup-step-exchange">
            <label for="setup-exchange">{localize(locale, MessageKey.SETUP_EXCHANGE)}</label>
            <input id="setup-exchange" name="exchange" value="{escape(settings.exchange.name)}">
            <span class="field-note">{localize(locale, MessageKey.SETTINGS_RELOAD_REQUIRED)}</span>
          </div>
"""


def _option(*, locale: Locale, value: str, option: str) -> str:
    selected = " selected" if value == option else ""
    label = localize(locale, SETUP_OPTION_LABELS[option])
    return f'<option value="{escape(option)}"{selected}>{escape(label)}</option>'


def _decimal(value: Decimal) -> str:
    rendered = format(value, "f")
    return rendered.rstrip("0").rstrip(".") if "." in rendered else rendered
