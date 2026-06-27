from __future__ import annotations

from decimal import Decimal

from nfi_engine.config import RuntimeSettings


def field_value(*, settings: RuntimeSettings, path: str) -> str:
    return field_values(settings).get(path, "")


def field_values(settings: RuntimeSettings) -> dict[str, str]:
    margin_mode = (
        "" if settings.exchange.margin_mode is None else settings.exchange.margin_mode.value
    )
    return {
        "exchange.name": settings.exchange.name,
        "exchange.trading_mode": settings.exchange.trading_mode.value,
        "exchange.margin_mode": margin_mode,
        "exchange.passphrase": settings.exchange.passphrase or "",
        "exchange.memo": settings.exchange.memo or "",
        "exchange.operator_id": settings.exchange.operator_id or "",
        "exchange.account_address": settings.exchange.account_address or "",
        "exchange.api_wallet_signer": settings.exchange.api_wallet_signer or "",
        "exchange.permission_read": settings.exchange.permission_read.value,
        "exchange.permission_trade": settings.exchange.permission_trade.value,
        "exchange.permission_futures": settings.exchange.permission_futures.value,
        "exchange.permission_withdrawal": settings.exchange.permission_withdrawal.value,
        "exchange.permission_ip_allowlist": settings.exchange.permission_ip_allowlist.value,
        "risk.risk_profile": settings.risk.risk_profile.value,
        "risk.expert_risk_confirmed": _bool(settings.risk.expert_risk_confirmed),
        "risk.stake_usdt": _decimal(settings.risk.stake_usdt),
        "risk.max_daily_loss_pct": _decimal(settings.risk.max_daily_loss_pct),
        "risk.allocation_cap_pct": _decimal(settings.risk.allocation_cap_pct),
        "risk.leverage": _decimal(settings.risk.leverage),
        "risk.max_leverage": _decimal(settings.risk.max_leverage),
        "risk.liquidation_buffer": _decimal(settings.risk.liquidation_buffer),
        "risk.max_open_trades": str(settings.risk.max_open_trades),
        "risk.stoploss_pct": _decimal(settings.risk.stoploss_pct),
        "risk.minimal_roi": _decimal(settings.risk.minimal_roi),
        "risk.cooldown_seconds": str(settings.risk.cooldown_seconds),
        "risk.locked_pairs": settings.risk.locked_pairs,
        "backtest.stoploss_pct": _decimal(settings.backtest.stoploss_pct),
        "backtest.fee_rate": _decimal(settings.backtest.fee_rate),
        "backtest.slippage_rate": _decimal(settings.backtest.slippage_rate),
        "backtest.max_open_trades": str(settings.backtest.max_open_trades),
        "ui.locale": settings.ui.locale.value,
        "ui.read_only": _bool(settings.ui.read_only),
        "logging.level": settings.logging.level.value,
        "notifications.enabled": _bool(settings.notifications.enabled),
        "notifications.jsonl_path": settings.notifications.jsonl_path,
        "notifications.timeout_seconds": _decimal(settings.notifications.timeout_seconds),
        "notifications.max_attempts": str(settings.notifications.max_attempts),
    }


def _decimal(value: Decimal) -> str:
    return format(value, "f")


def _bool(value: bool) -> str:
    return str(value).lower()
