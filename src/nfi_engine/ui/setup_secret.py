from __future__ import annotations

from html import escape

from nfi_engine.config import Locale
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_secret_step(
    *,
    test_id: str,
    label: str,
    field_id: str,
    name: str,
    locale: Locale,
) -> str:
    return f"""
          <div class="field-row" data-testid="{test_id}">
            <label for="{field_id}">{escape(label)}</label>
            <input id="{field_id}" name="{name}" type="password" autocomplete="off">
            <span class="field-note">{localize(locale, MessageKey.SETUP_WRITE_ONLY)}</span>
          </div>
"""
