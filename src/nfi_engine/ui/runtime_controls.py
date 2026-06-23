from __future__ import annotations

from html import escape

from nfi_engine.config import Locale, RuntimeSettings
from nfi_engine.paper import BotState
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_runtime_controls(
    *,
    settings: RuntimeSettings,
    locale: Locale,
    state: BotState = BotState.STOPPED,
) -> str:
    disabled = _disabled_attrs(settings)
    return (
        '<section data-testid="runtime-controls">\n'
        f"  <h2>{localize(locale, MessageKey.SETTINGS_RUNTIME_CONTROL_STATE)}</h2>\n"
        '  <div class="state" data-testid="runtime-control-state">'
        f"{escape(state.value)}</div>\n"
        '  <div class="state" data-testid="runtime-health-state">'
        f"{localize(locale, MessageKey.HOME_COCKPIT_RUNTIME_UNKNOWN)}</div>\n"
        '  <div class="toolbar">\n'
        f"    {_button('start-button', 'start', localize(locale, MessageKey.START), disabled)}\n"
        f"    {_button('pause-button', 'pause', localize(locale, MessageKey.PAUSE), disabled)}\n"
        f"    {_button('resume-button', 'resume', localize(locale, MessageKey.RESUME), disabled)}\n"
        f"    {_button('stop-button', 'stop', localize(locale, MessageKey.STOP), disabled)}\n"
        "  </div>\n"
        "</section>\n"
    )


def _button(test_id: str, command: str, label: str, disabled: str) -> str:
    return (
        f'<button type="button" data-testid="{escape(test_id)}"{disabled} '
        f'data-command="{escape(command)}">{escape(label)}</button>'
    )


def _disabled_attrs(settings: RuntimeSettings) -> str:
    if not settings.ui.read_only:
        return ""
    title = escape(localize(settings.ui.locale, MessageKey.SETTINGS_READONLY_DISABLED_TITLE))
    return f' disabled title="{title}"'
