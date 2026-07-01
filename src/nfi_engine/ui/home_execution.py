from __future__ import annotations

from html import escape
from typing import Final

from nfi_engine.config import Locale
from nfi_engine.safety.execution_signals import (
    EXECUTION_SAFETY_SIGNALS,
    ExecutionSafetySignalDefinition,
)
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey

_SIGNAL_LABEL_KEYS: Final[dict[str, MessageKey]] = {
    "order_lifecycle": MessageKey.HOME_EXECUTION_SIGNAL_ORDER_LIFECYCLE,
    "reconciliation": MessageKey.HOME_EXECUTION_SIGNAL_RECONCILIATION,
    "idempotency": MessageKey.HOME_EXECUTION_SIGNAL_IDEMPOTENCY,
    "kill_switch": MessageKey.HOME_EXECUTION_SIGNAL_KILL_SWITCH,
    "circuit_breakers": MessageKey.HOME_EXECUTION_SIGNAL_CIRCUIT_BREAKERS,
    "partial_fill_exposure": MessageKey.HOME_EXECUTION_SIGNAL_PARTIAL_FILL_EXPOSURE,
}


def render_execution_safety_signals(*, locale: Locale) -> str:
    rows = "\n".join(_signal_row(signal, locale=locale) for signal in EXECUTION_SAFETY_SIGNALS)
    return (
        '<section class="execution-safety" data-testid="execution-safety-signals">\n'
        f"  <h2>{localize(locale, MessageKey.HOME_EXECUTION_SAFETY_TITLE)}</h2>\n"
        f'  <div class="state">{_signal_count(locale=locale)}</div>\n'
        f'  <ul class="signal-list">{rows}</ul>\n'
        "</section>\n"
    )


def execution_safety_summary(*, locale: Locale) -> str:
    return _signal_count(locale=locale)


def _signal_count(*, locale: Locale) -> str:
    required = localize(locale, MessageKey.HOME_EXECUTION_SIGNAL_REQUIRED)
    return f"{len(EXECUTION_SAFETY_SIGNALS)} {required}"


def _signal_row(signal: ExecutionSafetySignalDefinition, *, locale: Locale) -> str:
    label_key = _SIGNAL_LABEL_KEYS[signal.code]
    return (
        f'<li data-testid="execution-signal-{escape(signal.code)}">'
        f"<strong>{escape(localize(locale, label_key))}</strong>"
        f"<span>{localize(locale, MessageKey.HOME_EXECUTION_SIGNAL_REQUIRED)}</span>"
        "</li>"
    )
