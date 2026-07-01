from __future__ import annotations

import json
from hashlib import sha256

from nfi_engine.config import RuntimeSettings
from nfi_engine.exchange.live_canary_checks import LIVE_CANARY_CONFIRMATION_PHRASE


def live_canary_preview_hash(settings: RuntimeSettings) -> str:
    payload = _canonical_preview_payload(settings)
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    return sha256(encoded).hexdigest()


def _canonical_preview_payload(settings: RuntimeSettings) -> dict[str, str | int | bool | None]:
    canary = settings.live_canary
    return {
        "exchange": settings.exchange.name,
        "exchange_testnet": settings.exchange.testnet,
        "engine_live_trading": settings.engine.live_trading,
        "trading_mode": _value(canary.trading_mode),
        "exchange_trading_mode": settings.exchange.trading_mode.value,
        "pair": canary.pair,
        "order_type": _value(canary.order_type),
        "canary_notional_usdt": _decimal_text(canary.canary_notional_usdt),
        "leverage": _decimal_text(canary.leverage),
        "confirmation_phrase": canary.confirmation_phrase,
        "required_confirmation_phrase": LIVE_CANARY_CONFIRMATION_PHRASE,
        "reconciliation_captured_at": _datetime_text(canary.reconciliation_captured_at),
        "wallet_balance_captured_at": _datetime_text(canary.wallet_balance_captured_at),
        "manual_halt_file": settings.circuit_breakers.manual_halt_file,
        "max_stale_seconds": settings.circuit_breakers.max_stale_seconds,
        "stoploss_pct": _decimal_text(settings.risk.stoploss_pct),
        "fee_rate": _decimal_text(settings.backtest.fee_rate),
    }


def _decimal_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _datetime_text(value: object) -> str | None:
    if value is None:
        return None
    return str(value)


def _value(value: object) -> str | None:
    if value is None:
        return None
    return str(value)
