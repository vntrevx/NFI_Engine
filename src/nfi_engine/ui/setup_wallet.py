from __future__ import annotations

from nfi_engine.config import Locale
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_wallet_step(*, locale: Locale) -> str:
    return f"""
          <div class="field-row" data-testid="setup-step-wallet-balance">
            <label for="setup-wallet-state">\
{localize(locale, MessageKey.HOME_COCKPIT_WALLET_BALANCE)}</label>
            <div class="inline-state" id="setup-wallet-state" data-testid="wallet-balance-state">
              {localize(locale, MessageKey.SETUP_WALLET_NOT_FETCHED)}
            </div>
            <button type="button" data-testid="wallet-fetch-button">\
{localize(locale, MessageKey.SETUP_FETCH_WALLET)}</button>
          </div>
"""
