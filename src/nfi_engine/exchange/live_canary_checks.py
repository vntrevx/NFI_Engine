from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Final

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import DomainError, Leverage, TradingMode, TradingPair
from nfi_engine.exchange.credential_requirements import missing_runtime_credential_fields
from nfi_engine.exchange.live_canary_models import (
    LiveCanaryCheck,
    LiveCanaryCheckCode,
    LiveCanaryCheckState,
)
from nfi_engine.exchange.permissions import ExchangeApiPermissionState
from nfi_engine.wallet import WalletPermissionAuditSnapshot

LIVE_CANARY_CONFIRMATION_PHRASE: Final = "CONFIRM_LIVE_CANARY_PREVIEW"
PERMISSION_NEXT_ACTION: Final = (
    "Enable read/trade/futures as needed, disable withdrawal, " + "and require IP allowlist proof."
)


def static_preview_checks(settings: RuntimeSettings) -> tuple[LiveCanaryCheck, ...]:
    return (
        enabled_check(settings),
        production_scope_check(settings),
        required_fields_check(settings),
        pair_check(settings),
        confirmation_check(settings),
        credentials_check(settings),
        permissions_check(settings),
        manual_halt_check(settings),
    )


def enabled_check(settings: RuntimeSettings) -> LiveCanaryCheck:
    if settings.live_canary.enabled:
        return clear(
            LiveCanaryCheckCode.CONFIG_ENABLED,
            "live_canary.enabled=true",
            "No live canary config action required.",
        )
    return block(
        LiveCanaryCheckCode.CONFIG_ENABLED,
        "live_canary.enabled=false",
        "Set live_canary.enabled=true only for an explicit canary preview.",
    )


def production_scope_check(settings: RuntimeSettings) -> LiveCanaryCheck:
    if settings.engine.live_trading:
        return block(
            LiveCanaryCheckCode.PRODUCTION_SCOPE,
            "engine.live_trading must remain false for preview",
            "Use the live_canary section, not default runtime live_trading startup.",
        )
    if settings.exchange.testnet:
        return block(
            LiveCanaryCheckCode.PRODUCTION_SCOPE,
            "exchange.testnet=true",
            "Set exchange.testnet=false only for an owner-approved live canary preview.",
        )
    return clear(
        LiveCanaryCheckCode.PRODUCTION_SCOPE,
        "exchange.testnet=false and engine.live_trading=false",
        "No production-scope preview action required.",
    )


def required_fields_check(settings: RuntimeSettings) -> LiveCanaryCheck:
    missing = _required_field_issues(settings)
    canary = settings.live_canary
    if missing:
        return block(
            LiveCanaryCheckCode.REQUIRED_FIELDS,
            f"missing={','.join(missing)}",
            "Set every live_canary field explicitly before previewing.",
        )
    if canary.trading_mode is not settings.exchange.trading_mode:
        return block(
            LiveCanaryCheckCode.REQUIRED_FIELDS,
            "live_canary.trading_mode must match exchange.trading_mode",
            "Align live_canary.trading_mode with the exchange config.",
        )
    return clear(
        LiveCanaryCheckCode.REQUIRED_FIELDS,
        "required live_canary fields are explicit",
        "No required-field action needed.",
    )


def pair_check(settings: RuntimeSettings) -> LiveCanaryCheck:
    canary = settings.live_canary
    if canary.pair is None or canary.trading_mode is None:
        return block(
            LiveCanaryCheckCode.PAIR_VALID,
            "pair_or_mode_missing",
            "Set live_canary.pair and live_canary.trading_mode.",
        )
    try:
        TradingPair.parse(canary.pair, canary.trading_mode)
        if canary.leverage is not None:
            Leverage.parse(canary.leverage)
    except DomainError as exc:
        return block(LiveCanaryCheckCode.PAIR_VALID, exc.code.value, exc.message)
    if canary.leverage is not None and canary.leverage > settings.risk.max_leverage:
        return block(
            LiveCanaryCheckCode.PAIR_VALID,
            "live_canary.leverage exceeds risk.max_leverage",
            "Lower live_canary.leverage or explicitly raise the risk max after review.",
        )
    return clear(
        LiveCanaryCheckCode.PAIR_VALID,
        "pair and leverage parse at the domain boundary",
        "No pair/leverage action required.",
    )


def confirmation_check(settings: RuntimeSettings) -> LiveCanaryCheck:
    phrase = settings.live_canary.confirmation_phrase
    if phrase is None or phrase.strip() == "":
        return block(
            LiveCanaryCheckCode.CONFIRMATION,
            "confirmation_phrase=missing",
            f"Set confirmation_phrase={LIVE_CANARY_CONFIRMATION_PHRASE}.",
        )
    if phrase != LIVE_CANARY_CONFIRMATION_PHRASE:
        return block(
            LiveCanaryCheckCode.CONFIRMATION,
            "confirmation_phrase=mismatch",
            f"Use the exact phrase {LIVE_CANARY_CONFIRMATION_PHRASE}.",
        )
    return clear(
        LiveCanaryCheckCode.CONFIRMATION,
        "confirmation phrase matches preview gate",
        "No confirmation action required.",
    )


def credentials_check(settings: RuntimeSettings) -> LiveCanaryCheck:
    missing = missing_runtime_credential_fields(settings)
    if missing:
        return block(
            LiveCanaryCheckCode.CREDENTIALS,
            f"missing={','.join(missing)}",
            "Load owner-only exchange credentials locally; do not commit them.",
        )
    return clear(
        LiveCanaryCheckCode.CREDENTIALS,
        "credential fields are present and redacted from preview",
        "No credential action required.",
    )


def permissions_check(settings: RuntimeSettings) -> LiveCanaryCheck:
    audit = WalletPermissionAuditSnapshot.from_settings(settings)
    required = _missing_permission_fields(settings)
    if audit.live_blocking_codes or required:
        blockers = (*audit.live_blocking_codes, *required)
        return block(
            LiveCanaryCheckCode.PERMISSIONS,
            f"permission_blockers={','.join(blockers)}",
            PERMISSION_NEXT_ACTION,
        )
    return clear(
        LiveCanaryCheckCode.PERMISSIONS,
        audit.summary,
        "No permission-hardening action required.",
    )


def manual_halt_check(settings: RuntimeSettings) -> LiveCanaryCheck:
    path = settings.circuit_breakers.manual_halt_file
    if path is None or path.strip() == "":
        return block(
            LiveCanaryCheckCode.MANUAL_HALT,
            "manual_halt_file=missing",
            "Configure circuit_breakers.manual_halt_file before live canary preview.",
        )
    if settings.circuit_breakers.manual_halt or Path(path).exists():
        return block(
            LiveCanaryCheckCode.MANUAL_HALT,
            "manual_halt=active",
            "Clear manual halt only after reviewing why it was set.",
        )
    return clear(
        LiveCanaryCheckCode.MANUAL_HALT,
        "manual halt path is configured and not active",
        "No kill-switch action required.",
    )


def normalized_pair(settings: RuntimeSettings) -> str | None:
    canary = settings.live_canary
    if canary.pair is None or canary.trading_mode is None:
        return canary.pair
    try:
        return str(TradingPair.parse(canary.pair, canary.trading_mode).normalized)
    except DomainError:
        return canary.pair


def kill_switch_state(settings: RuntimeSettings) -> str:
    path = settings.circuit_breakers.manual_halt_file
    if settings.circuit_breakers.manual_halt:
        return "blocked-manual-halt"
    if path is not None and Path(path).exists():
        return "blocked-halt-file"
    if path is None or path.strip() == "":
        return "missing-halt-file"
    return "armed"


def _required_field_issues(settings: RuntimeSettings) -> tuple[str, ...]:
    canary = settings.live_canary
    return tuple(
        issue
        for issue in (
            _positive_decimal_issue(
                canary.canary_notional_usdt,
                missing="canary_notional_usdt",
                nonpositive="canary_notional_usdt_positive",
            ),
            "pair" if _blank(canary.pair) else None,
            "trading_mode" if canary.trading_mode is None else None,
            _positive_decimal_issue(
                canary.leverage,
                missing="leverage",
                nonpositive="leverage_positive",
            ),
            "order_type" if canary.order_type is None else None,
            "confirmation_phrase" if canary.confirmation_phrase is None else None,
        )
        if issue is not None
    )


def _positive_decimal_issue(
    value: Decimal | None,
    *,
    missing: str,
    nonpositive: str,
) -> str | None:
    if value is None:
        return missing
    if value <= 0 or not value.is_finite():
        return nonpositive
    return None


def _missing_permission_fields(settings: RuntimeSettings) -> tuple[str, ...]:
    permission = settings.exchange
    missing: list[str] = []
    if permission.permission_read is not ExchangeApiPermissionState.ENABLED:
        missing.append("EXCHANGE_PERMISSION_READ_REQUIRED")
    if permission.permission_trade is not ExchangeApiPermissionState.ENABLED:
        missing.append("EXCHANGE_PERMISSION_TRADE_REQUIRED")
    if (
        settings.exchange.trading_mode is TradingMode.FUTURES
        and permission.permission_futures is not ExchangeApiPermissionState.ENABLED
    ):
        missing.append("EXCHANGE_PERMISSION_FUTURES_REQUIRED")
    if permission.permission_withdrawal is not ExchangeApiPermissionState.DISABLED:
        missing.append("EXCHANGE_PERMISSION_WITHDRAWAL_DISABLED_REQUIRED")
    if permission.permission_ip_allowlist is not ExchangeApiPermissionState.ENABLED:
        missing.append("EXCHANGE_PERMISSION_IP_ALLOWLIST_REQUIRED")
    return tuple(missing)


def _blank(value: str | None) -> bool:
    return value is None or value.strip() == ""


def clear(code: LiveCanaryCheckCode, message: str, next_action: str) -> LiveCanaryCheck:
    return LiveCanaryCheck(
        code=code, state=LiveCanaryCheckState.CLEAR, message=message, next_action=next_action
    )


def block(code: LiveCanaryCheckCode, message: str, next_action: str) -> LiveCanaryCheck:
    return LiveCanaryCheck(
        code=code, state=LiveCanaryCheckState.BLOCK, message=message, next_action=next_action
    )
