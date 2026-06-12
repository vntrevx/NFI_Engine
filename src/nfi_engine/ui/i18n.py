from __future__ import annotations

import json
from typing import Final

from nfi_engine.config import Locale
from nfi_engine.ui.i18n_el import EL_CATALOG
from nfi_engine.ui.i18n_en import EN_CATALOG
from nfi_engine.ui.i18n_keys import Catalog, MessageKey
from nfi_engine.ui.i18n_ko import KO_CATALOG

CATALOGS: Final[dict[Locale, Catalog]] = {
    Locale.EN: EN_CATALOG,
    Locale.KO: KO_CATALOG,
    Locale.EL: EL_CATALOG,
}
JS_KEYS: Final[tuple[MessageKey, ...]] = tuple(MessageKey)


def supported_locales() -> tuple[Locale, ...]:
    return (Locale.EN, Locale.KO, Locale.EL)


def localize(locale: Locale, key: MessageKey) -> str:
    catalog = CATALOGS.get(locale, EN_CATALOG)
    return catalog.get(key, EN_CATALOG[key])


def format_message(locale: Locale, key: MessageKey, **values: object) -> str:
    return localize(locale, key).format(**values)


def render_i18n_script(locale: Locale) -> str:
    payload = {key.value: localize(locale, key) for key in JS_KEYS}
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return f"<script>window.NFI_I18N={encoded};</script>\n"
