from __future__ import annotations

from html import escape
from typing import Final

from nfi_engine.config import Locale
from nfi_engine.dashboard import DashboardAction
from nfi_engine.ui.home_action_copy import action_copy
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey

ACTION_TARGET_HREFS: Final[dict[str, str]] = {
    "dashboard/status": "#status",
    "logs": "/logs",
    "logs/support-bundle": "/api/v1/reports/support-bundle.zip",
    "settings": "/settings",
    "settings/setup": "/settings",
}


def render_action_queue(actions: tuple[DashboardAction, ...], *, locale: Locale) -> str:
    rows = "\n".join(_action_row(action, locale=locale) for action in actions)
    if rows == "":
        rows = f'<li class="muted">{localize(locale, MessageKey.HOME_ACTION_EMPTY)}</li>'
    return (
        '<section data-testid="action-queue">\n'
        f"  <h2>{localize(locale, MessageKey.HOME_ACTION_QUEUE)}</h2>\n"
        f"  <ul>{rows}</ul>\n"
        "</section>\n"
    )


def _action_row(action: DashboardAction, *, locale: Locale) -> str:
    href = ACTION_TARGET_HREFS.get(action.target, "#status")
    title, detail = action_copy(action, locale=locale)
    return (
        f'<li data-testid="action-item" class="action-{escape(action.severity)}">'
        f"<strong>{escape(title)}</strong>"
        f"<span>{escape(detail)}</span>"
        f'<a href="{escape(href)}">{escape(action.target)}</a>'
        "</li>"
    )
