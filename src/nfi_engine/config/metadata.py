from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final


class FieldGroup(StrEnum):
    SIMPLE = "simple"
    ADVANCED = "advanced"


@dataclass(frozen=True, slots=True)
class FieldMetadata:
    path: str
    frontend_editable: bool
    sensitive: bool
    restart_required: bool
    runtime_apply_safe: bool
    ui_group: FieldGroup


def _locked(path: str, *, ui_group: FieldGroup = FieldGroup.ADVANCED) -> FieldMetadata:
    return FieldMetadata(
        path=path,
        frontend_editable=False,
        sensitive=False,
        restart_required=True,
        runtime_apply_safe=False,
        ui_group=ui_group,
    )


def _restart(
    path: str,
    *,
    sensitive: bool = False,
    ui_group: FieldGroup = FieldGroup.ADVANCED,
) -> FieldMetadata:
    return FieldMetadata(
        path=path,
        frontend_editable=True,
        sensitive=sensitive,
        restart_required=True,
        runtime_apply_safe=False,
        ui_group=ui_group,
    )


def _safe(
    path: str,
    *,
    sensitive: bool = False,
    ui_group: FieldGroup = FieldGroup.ADVANCED,
) -> FieldMetadata:
    return FieldMetadata(
        path=path,
        frontend_editable=True,
        sensitive=sensitive,
        restart_required=False,
        runtime_apply_safe=True,
        ui_group=ui_group,
    )


FIELD_METADATA: Final[tuple[FieldMetadata, ...]] = (
    _locked("engine.live_trading"),
    _restart("exchange.name", ui_group=FieldGroup.SIMPLE),
    _restart("exchange.trading_mode", ui_group=FieldGroup.SIMPLE),
    _restart("exchange.margin_mode"),
    _restart("exchange.api_key", sensitive=True),
    _restart("exchange.api_secret", sensitive=True),
    _safe("risk.stake_usdt", ui_group=FieldGroup.SIMPLE),
    _safe("risk.risk_profile", ui_group=FieldGroup.SIMPLE),
    _safe("risk.expert_risk_confirmed"),
    _safe("risk.max_daily_loss_pct"),
    _safe("risk.allocation_cap_pct"),
    _safe("risk.leverage"),
    _safe("risk.max_leverage"),
    _safe("risk.liquidation_buffer"),
    _safe("risk.max_open_trades", ui_group=FieldGroup.SIMPLE),
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
    _safe("ui.locale", ui_group=FieldGroup.SIMPLE),
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
                f"ui_group={item.ui_group.value}",
            ),
        )
        for item in FIELD_METADATA
    )
