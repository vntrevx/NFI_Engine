from __future__ import annotations

from html import escape

from nfi_engine.config import RuntimeSettings
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_pairlist_panel(settings: RuntimeSettings, *, read_only: bool = False) -> str:
    locale = settings.ui.locale
    blacklist = escape(settings.pairlist.blacklist)
    disabled = _disabled_attrs(read_only, settings=settings)
    return (
        '<section data-testid="pairlist-panel">\n'
        f"  <h2>{localize(locale, MessageKey.PAIRLIST_TITLE)}</h2>\n"
        '  <div class="log-tools">\n'
        f"    <label>{localize(locale, MessageKey.PAIRLIST_BLACKLIST)}\n"
        "      <input\n"
        '        data-testid="pairlist-blacklist"\n'
        f'        value="{blacklist}"\n'
        f'        aria-label="{localize(locale, MessageKey.PAIRLIST_BLACKLIST_ARIA)}"\n'
        "      >\n"
        "    </label>\n"
        '    <button type="button" data-testid="pairlist-preview-button">'
        f"{localize(locale, MessageKey.PREVIEW)}</button>\n"
        f'    <button data-testid="pairlist-save-draft-button"{disabled} type="button">'
        f"{localize(locale, MessageKey.SAVE_DRAFT)}</button>\n"
        f'    <button data-testid="pairlist-apply-button"{disabled} type="button" class="primary">'
        f"{localize(locale, MessageKey.APPLY)}</button>\n"
        "  </div>\n"
        '  <div class="state detail" data-testid="pairlist-preview-state">'
        f"{localize(locale, MessageKey.PAIRLIST_PREVIEW_EMPTY)}</div>\n"
        '  <div class="audit" data-testid="pairlist-audit-log">'
        f"{localize(locale, MessageKey.PAIRLIST_AUDIT_EMPTY)}</div>\n"
        "</section>\n"
    )


def _disabled_attrs(read_only: bool, *, settings: RuntimeSettings) -> str:
    if not read_only:
        return ""
    title = escape(localize(settings.ui.locale, MessageKey.SETTINGS_READONLY_DISABLED_TITLE))
    return f' disabled title="{title}"'
