from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class FieldMetadata:
    path: str
    frontend_editable: bool
    sensitive: bool
    restart_required: bool
    runtime_apply_safe: bool


def _locked(path: str) -> FieldMetadata:
    return FieldMetadata(
        path=path,
        frontend_editable=False,
        sensitive=False,
        restart_required=True,
        runtime_apply_safe=False,
    )


def _restart(path: str, *, sensitive: bool = False) -> FieldMetadata:
    return FieldMetadata(
        path=path,
        frontend_editable=True,
        sensitive=sensitive,
        restart_required=True,
        runtime_apply_safe=False,
    )


def _safe(path: str, *, sensitive: bool = False) -> FieldMetadata:
    return FieldMetadata(
        path=path,
        frontend_editable=True,
        sensitive=sensitive,
        restart_required=False,
        runtime_apply_safe=True,
    )


FIELD_METADATA: Final[tuple[FieldMetadata, ...]] = (
    _locked("engine.live_trading"),
    _restart("exchange.name"),
    _restart("exchange.trading_mode"),
    _restart("exchange.margin_mode"),
    _restart("exchange.api_key", sensitive=True),
    _restart("exchange.api_secret", sensitive=True),
    _safe("risk.stake_usdt"),
    _safe("risk.max_daily_loss_pct"),
    _safe("risk.leverage"),
    _safe("risk.max_leverage"),
    _safe("risk.liquidation_buffer"),
    _safe("risk.max_open_trades"),
    _safe("risk.stoploss_pct"),
    _safe("risk.minimal_roi"),
    _safe("risk.cooldown_seconds"),
    _safe("risk.locked_pairs"),
    _safe("backtest.stoploss_pct"),
    _safe("backtest.fee_rate"),
    _safe("backtest.slippage_rate"),
    _safe("backtest.max_open_trades"),
    _locked("api.host"),
    _locked("api.port"),
    _restart("api.auth_token", sensitive=True),
    _safe("ui.read_only"),
    _safe("logging.level"),
    _safe("notifications.enabled"),
    _safe("notifications.jsonl_path"),
    _safe("notifications.webhook_url", sensitive=True),
    _safe("notifications.discord_webhook_url", sensitive=True),
    _safe("notifications.telegram_bot_token", sensitive=True),
    _safe("notifications.telegram_chat_id", sensitive=True),
    _safe("notifications.timeout_seconds"),
    _safe("notifications.max_attempts"),
)


def frontend_metadata() -> tuple[FieldMetadata, ...]:
    return FIELD_METADATA


def render_frontend_metadata() -> tuple[str, ...]:
    return tuple(
        " ".join(
            (
                f"field={item.path}",
                f"frontend_editable={str(item.frontend_editable).lower()}",
                f"sensitive={str(item.sensitive).lower()}",
                f"restart_required={str(item.restart_required).lower()}",
                f"runtime_apply_safe={str(item.runtime_apply_safe).lower()}",
            ),
        )
        for item in FIELD_METADATA
    )
