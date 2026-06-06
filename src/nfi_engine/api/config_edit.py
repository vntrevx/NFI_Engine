from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Final

from nfi_engine.api.models import ConfigFieldPatch
from nfi_engine.config import FieldMetadata, LogLevel, frontend_metadata

POSITIVE_INT_FIELDS: Final = frozenset(
    ("risk.max_open_trades", "risk.cooldown_seconds", "backtest.max_open_trades")
)
POSITIVE_DECIMAL_FIELDS: Final = frozenset(
    (
        "risk.stake_usdt",
        "risk.max_daily_loss_pct",
        "risk.leverage",
        "risk.max_leverage",
        "risk.liquidation_buffer",
        "risk.stoploss_pct",
        "risk.minimal_roi",
        "backtest.stoploss_pct",
        "backtest.fee_rate",
        "backtest.slippage_rate",
        "notifications.timeout_seconds",
    )
)
BOOLEAN_FIELDS: Final = frozenset(("ui.read_only", "notifications.enabled"))


@dataclass(frozen=True, slots=True)
class ConfigPatchCheck:
    valid: bool
    errors: tuple[str, ...]
    restart_required: bool


def check_config_patch(fields: tuple[ConfigFieldPatch, ...]) -> ConfigPatchCheck:
    errors: list[str] = []
    restart_required = False
    for field in fields:
        metadata = _metadata_for(field.path)
        if metadata is None:
            errors.append(f"{field.path} is not a known frontend setting")
            continue
        if metadata.restart_required:
            restart_required = True
        errors.extend(_metadata_errors(field=field, metadata=metadata))
        errors.extend(_value_errors(field))
    return ConfigPatchCheck(
        valid=len(errors) == 0,
        errors=tuple(errors),
        restart_required=restart_required,
    )


def _metadata_for(path: str) -> FieldMetadata | None:
    for item in frontend_metadata():
        if item.path == path:
            return item
    return None


def _metadata_errors(*, field: ConfigFieldPatch, metadata: FieldMetadata) -> tuple[str, ...]:
    if field.path == "engine.live_trading":
        return ("engine.live_trading is locked for milestone 1",)
    if metadata.sensitive:
        return (f"{field.path} is sensitive and hidden",)
    if not metadata.frontend_editable:
        return (f"{field.path} is locked",)
    return ()


def _value_errors(field: ConfigFieldPatch) -> tuple[str, ...]:
    if field.path in POSITIVE_INT_FIELDS:
        return _positive_int_errors(field)
    if field.path == "notifications.max_attempts":
        return _min_int_errors(field, minimum=1)
    if field.path in POSITIVE_DECIMAL_FIELDS:
        return _positive_decimal_errors(field)
    if field.path in BOOLEAN_FIELDS:
        return _boolean_errors(field)
    if field.path == "logging.level":
        return _log_level_errors(field)
    return ()


def _positive_int_errors(field: ConfigFieldPatch) -> tuple[str, ...]:
    return _min_int_errors(field, minimum=0)


def _min_int_errors(field: ConfigFieldPatch, *, minimum: int) -> tuple[str, ...]:
    try:
        value = int(field.value)
    except ValueError:
        return (f"{field.path} must be an integer",)
    if value < minimum:
        return (f"{field.path} must be at least {minimum}",)
    if field.path == "risk.max_open_trades" and value < 1:
        return ("risk.max_open_trades must be at least 1",)
    if field.path == "backtest.max_open_trades" and value < 1:
        return ("backtest.max_open_trades must be at least 1",)
    return ()


def _positive_decimal_errors(field: ConfigFieldPatch) -> tuple[str, ...]:
    try:
        value = Decimal(field.value)
    except InvalidOperation:
        return (f"{field.path} must be numeric",)
    if value < 0:
        return (f"{field.path} must be zero or greater",)
    return ()


def _boolean_errors(field: ConfigFieldPatch) -> tuple[str, ...]:
    normalized = field.value.lower()
    if normalized in {"true", "false"}:
        return ()
    return (f"{field.path} must be true or false",)


def _log_level_errors(field: ConfigFieldPatch) -> tuple[str, ...]:
    if field.value in {level.value for level in LogLevel}:
        return ()
    return (f"{field.path} must be DEBUG, INFO, WARNING, or ERROR",)
