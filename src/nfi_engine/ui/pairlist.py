from __future__ import annotations

from html import escape

from nfi_engine.config import RuntimeSettings


def render_pairlist_panel(settings: RuntimeSettings, *, read_only: bool = False) -> str:
    blacklist = escape(settings.pairlist.blacklist)
    disabled = _disabled_attrs(read_only)
    return (
        '<section data-testid="pairlist-panel">\n'
        "  <h2>Pairlist</h2>\n"
        '  <div class="log-tools">\n'
        "    <label>Blacklist\n"
        "      <input\n"
        '        data-testid="pairlist-blacklist"\n'
        f'        value="{blacklist}"\n'
        '        aria-label="pairlist blacklist"\n'
        "      >\n"
        "    </label>\n"
        '    <button type="button" data-testid="pairlist-preview-button">'
        "Preview</button>\n"
        f'    <button data-testid="pairlist-save-draft-button"{disabled} type="button">'
        "Save draft</button>\n"
        f'    <button data-testid="pairlist-apply-button"{disabled} type="button" class="primary">'
        "Apply</button>\n"
        "  </div>\n"
        '  <div class="state detail" data-testid="pairlist-preview-state">'
        "No pairlist preview</div>\n"
        '  <div class="audit" data-testid="pairlist-audit-log">No pairlist audit event</div>\n'
        "</section>\n"
    )


def _disabled_attrs(read_only: bool) -> str:
    if not read_only:
        return ""
    return ' disabled title="Read-only mode blocks changes"'
