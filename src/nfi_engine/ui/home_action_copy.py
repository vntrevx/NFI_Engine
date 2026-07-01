from __future__ import annotations

from typing import Final

from nfi_engine.config import Locale
from nfi_engine.dashboard import DashboardAction
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey

_ACTION_COPY_KEYS: Final[dict[str, tuple[MessageKey, MessageKey]]] = {
    "readiness_blocked": (
        MessageKey.HOME_ACTION_READINESS_BLOCKED_TITLE,
        MessageKey.HOME_ACTION_READINESS_BLOCKED_DETAIL,
    ),
    "runtime_errors_detected": (
        MessageKey.HOME_ACTION_RUNTIME_ERRORS_TITLE,
        MessageKey.HOME_ACTION_RUNTIME_ERRORS_DETAIL,
    ),
    "pairlist_empty": (
        MessageKey.HOME_ACTION_PAIRLIST_EMPTY_TITLE,
        MessageKey.HOME_ACTION_PAIRLIST_EMPTY_DETAIL,
    ),
    "paper_runtime_ready": (
        MessageKey.HOME_ACTION_PAPER_READY_TITLE,
        MessageKey.HOME_ACTION_PAPER_READY_DETAIL,
    ),
    "preflight_not_loaded": (
        MessageKey.HOME_ACTION_PREFLIGHT_MISSING_TITLE,
        MessageKey.HOME_ACTION_PREFLIGHT_MISSING_DETAIL,
    ),
    "support_bundle_follow_up": (
        MessageKey.HOME_ACTION_SUPPORT_BUNDLE_TITLE,
        MessageKey.HOME_ACTION_SUPPORT_BUNDLE_DETAIL,
    ),
}


def action_copy(action: DashboardAction, *, locale: Locale) -> tuple[str, str]:
    keys = _ACTION_COPY_KEYS.get(action.code)
    if keys is None:
        return action.title, action.detail
    title_key, detail_key = keys
    return localize(locale, title_key), localize(locale, detail_key)


def action_title(action: DashboardAction, *, locale: Locale) -> str:
    title, _ = action_copy(action, locale=locale)
    return title
