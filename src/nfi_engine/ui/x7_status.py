from __future__ import annotations

from html import escape

from nfi_engine.config import Locale
from nfi_engine.strategy.nfi_x7 import X7SemanticStatus
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey


def render_x7_semantic_status(
    status: X7SemanticStatus | None,
    *,
    locale: Locale,
) -> str:
    if status is None or not status.enabled:
        return ""
    rows = "\n".join(
        _item(test_id, localize(locale, label), value) for test_id, label, value in _items(status)
    )
    return (
        '<section class="x7-status" data-testid="x7-semantic-status">\n'
        f"  <h2>{localize(locale, MessageKey.HOME_X7_TITLE)}</h2>\n"
        f"  <p>{localize(locale, MessageKey.HOME_X7_DESCRIPTION)}</p>\n"
        '  <div class="x7-status-grid">\n'
        f"    {rows}\n"
        "  </div>\n"
        f"  {_blocked_reason(status, locale=locale)}\n"
        f'  <div class="state" data-testid="x7-next-action">{escape(status.next_action)}</div>\n'
        "</section>\n"
    )


def _blocked_reason(status: X7SemanticStatus, *, locale: Locale) -> str:
    if status.blocked_reason is None:
        return ""
    label = localize(locale, MessageKey.HOME_X7_BLOCKED_REASON)
    return (
        '<div class="lock" data-testid="x7-blocked-reason">'
        f"<strong>{escape(label)}</strong> {escape(status.blocked_reason)}</div>\n"
    )


def _item(test_id: str, label: str, value: str) -> str:
    return (
        f'<div class="x7-status-item" data-testid="{escape(test_id)}">'
        f"<span>{escape(label)}</span><strong>{escape(value)}</strong></div>"
    )


def _items(status: X7SemanticStatus) -> tuple[tuple[str, MessageKey, str], ...]:
    return (
        ("x7-coverage", MessageKey.HOME_X7_COVERAGE, status.coverage_state.value),
        ("x7-provenance", MessageKey.HOME_X7_PROVENANCE, status.observed_upstream_version),
        ("x7-latest-signal", MessageKey.HOME_X7_LATEST_SIGNAL, status.latest_signal_reason),
        ("x7-warmup", MessageKey.HOME_X7_WARMUP, status.warmup_state),
        ("x7-missing-data", MessageKey.HOME_X7_MISSING_DATA, status.missing_data_state),
        ("x7-live-readiness", MessageKey.HOME_X7_LIVE_READINESS, status.live_readiness.value),
    )
