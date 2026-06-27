from __future__ import annotations

from html import escape
from typing import Final

from nfi_engine.config import Locale
from nfi_engine.setup.credentials import EXTRA_EXCHANGE_CREDENTIAL_FIELDS
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey
from nfi_engine.ui.setup_secret import render_secret_step

EXTRA_FIELD_LABELS: Final[dict[str, str]] = {
    "passphrase": "API passphrase",
    "memo": "API memo",
    "operator_id": "Operator ID",
    "account_address": "Account address",
    "api_wallet_signer": "API wallet signer",
}


def render_extra_credential_steps(*, locale: Locale) -> str:
    summary = escape(localize(locale, MessageKey.SETTINGS_EXCHANGE_OFFICIAL_CREDENTIALS))
    steps = "\n".join(
        render_secret_step(
            test_id=f"setup-step-{field.replace('_', '-')}",
            label=EXTRA_FIELD_LABELS[field],
            field_id=f"setup-{field.replace('_', '-')}",
            name=field,
            locale=locale,
        )
        for field in EXTRA_EXCHANGE_CREDENTIAL_FIELDS
    )
    return f"""
          <details class="setup-credential-drawer" data-testid="setup-step-extra-credentials">
            <summary>{summary}</summary>
{steps}
          </details>
"""
