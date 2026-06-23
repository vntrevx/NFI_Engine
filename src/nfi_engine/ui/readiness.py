from __future__ import annotations

from html import escape
from typing import Final

from nfi_engine.config import Locale
from nfi_engine.preflight.models import PreflightCode, PreflightReport, PreflightStatus
from nfi_engine.ui.i18n import format_message, localize
from nfi_engine.ui.i18n_keys import MessageKey

READINESS_MESSAGE_KEYS: Final[dict[PreflightCode, MessageKey]] = {
    PreflightCode.CONFIG_INVALID: MessageKey.READINESS_CONFIG_INVALID,
    PreflightCode.CONFIG_VALID: MessageKey.READINESS_CONFIG_VALID,
    PreflightCode.DB_PATH_MISSING: MessageKey.READINESS_DB_PATH_MISSING,
    PreflightCode.DB_PATH_READY: MessageKey.READINESS_DB_PATH_READY,
    PreflightCode.DOCKER_VOLUMES_MISSING: MessageKey.READINESS_DOCKER_VOLUMES_MISSING,
    PreflightCode.DOCKER_VOLUMES_READY: MessageKey.READINESS_DOCKER_VOLUMES_READY,
    PreflightCode.EXCHANGE_PERMISSION_AUDIT: MessageKey.READINESS_EXCHANGE_PERMISSION_AUDIT,
    PreflightCode.EXCHANGE_TESTNET_REQUIRED: MessageKey.READINESS_EXCHANGE_TESTNET_REQUIRED,
    PreflightCode.FUTURES_LEVERAGE_INVALID: MessageKey.READINESS_FUTURES_LEVERAGE_INVALID,
    PreflightCode.LIVE_CIRCUIT_BREAKER_HARDENING: (
        MessageKey.READINESS_LIVE_CIRCUIT_BREAKER_HARDENING
    ),
    PreflightCode.LIVE_EXCHANGE_CREDENTIALS: MessageKey.READINESS_LIVE_EXCHANGE_CREDENTIALS,
    PreflightCode.LIVE_PERMISSION_HARDENING: MessageKey.READINESS_LIVE_PERMISSION_HARDENING,
    PreflightCode.LIVE_RECONCILIATION_HARDENING: (
        MessageKey.READINESS_LIVE_RECONCILIATION_HARDENING
    ),
    PreflightCode.LIVE_STRATEGY_HARDENING: MessageKey.READINESS_LIVE_STRATEGY_HARDENING,
    PreflightCode.LIVE_TRADING_DISABLED: MessageKey.READINESS_LIVE_TRADING_DISABLED,
    PreflightCode.LIVE_TRADING_OUT_OF_SCOPE: MessageKey.READINESS_LIVE_TRADING_OUT_OF_SCOPE,
    PreflightCode.LOG_PATH_NOT_WRITABLE: MessageKey.READINESS_LOG_PATH_NOT_WRITABLE,
    PreflightCode.LOG_PATH_READY: MessageKey.READINESS_LOG_PATH_READY,
    PreflightCode.NOTIFIER_DISABLED: MessageKey.READINESS_NOTIFIER_DISABLED,
    PreflightCode.NOTIFIER_DRY_RUN_READY: MessageKey.READINESS_NOTIFIER_DRY_RUN_READY,
    PreflightCode.PAIR_CONFIG_VALID: MessageKey.READINESS_PAIR_CONFIG_VALID,
    PreflightCode.PROFILE_COMPATIBLE: MessageKey.READINESS_PROFILE_COMPATIBLE,
    PreflightCode.PROFILE_CONFIG_MISMATCH: MessageKey.READINESS_PROFILE_CONFIG_MISMATCH,
    PreflightCode.PUBLIC_BIND_NOT_ALLOWED: MessageKey.READINESS_PUBLIC_BIND_NOT_ALLOWED,
    PreflightCode.RECONCILIATION_READY: MessageKey.READINESS_RECONCILIATION_READY,
    PreflightCode.RECONCILIATION_REQUIRED: MessageKey.READINESS_RECONCILIATION_REQUIRED,
    PreflightCode.RISK_PROFILE_GUARDRAILS: MessageKey.READINESS_RISK_PROFILE_GUARDRAILS,
    PreflightCode.WEAK_API_TOKEN: MessageKey.READINESS_WEAK_API_TOKEN,
}


def render_readiness_panel(
    readiness: PreflightReport | None,
    *,
    locale: Locale = Locale.EN,
) -> str:
    if readiness is None:
        return _html_lines(
            [
                '<section data-testid="readiness-panel">',
                f"  <h2>{localize(locale, MessageKey.READINESS_TITLE)}</h2>",
                f'  <div class="state">{localize(locale, MessageKey.READINESS_EMPTY)}</div>',
                "</section>",
            ],
        )
    summary = "PREFLIGHT_BLOCKED" if readiness.blocked else "PREFLIGHT_PASSED"
    start_state = localize(
        locale,
        MessageKey.COMMON_BLOCKED if readiness.blocked else MessageKey.COMMON_READY,
    )
    return _html_lines(
        [
            '<section data-testid="readiness-panel">',
            f"  <h2>{localize(locale, MessageKey.READINESS_TITLE)}</h2>",
            f'  <div class="state" data-testid="readiness-summary">{summary}</div>',
            "  "
            + _group(
                readiness,
                PreflightStatus.PASS,
                "readiness-pass",
                MessageKey.COMMON_PASSED,
                locale,
            ),
            "  "
            + _group(
                readiness,
                PreflightStatus.WARN,
                "readiness-warn",
                MessageKey.COMMON_WARN,
                locale,
            ),
            "  "
            + _group(
                readiness,
                PreflightStatus.BLOCK,
                "readiness-block",
                MessageKey.COMMON_BLOCK,
                locale,
            ),
            (
                '  <div class="lock" data-testid="readiness-start-blocked">'
                f"{
                    format_message(
                        locale,
                        MessageKey.READINESS_START_STATE,
                        state=start_state,
                    )
                }</div>"
            ),
            "</section>",
        ],
    )


def _group(
    report: PreflightReport,
    status: PreflightStatus,
    test_id: str,
    label_key: MessageKey,
    locale: Locale,
) -> str:
    rows = "\n".join(
        _check_row(
            code=check.code.value,
            message=localize(locale, READINESS_MESSAGE_KEYS[check.code]),
        )
        for check in report.checks
        if check.status is status
    )
    if rows == "":
        rows = f'<li class="muted">{localize(locale, MessageKey.COMMON_NONE)}</li>'
    return _html_lines(
        [
            f'<div data-testid="{escape(test_id)}">',
            f"  <h3>{localize(locale, label_key)}</h3>",
            f"  <ul>{rows}</ul>",
            "</div>",
        ],
    )


def _check_row(*, code: str, message: str) -> str:
    return f"<li><strong>{escape(code)}</strong> {escape(message)}</li>"


def _html_lines(lines: list[str]) -> str:
    return "\n".join(lines)
