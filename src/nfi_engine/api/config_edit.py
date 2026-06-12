from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Final

from nfi_engine.api.models import ConfigFieldPatch
from nfi_engine.config import FieldMetadata, Locale, LogLevel, RuntimeSettings, frontend_metadata

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
LOCALE_VALUES: Final = frozenset(locale.value for locale in Locale)
FieldValue = bool | int | str | Decimal | Locale | LogLevel
ValueParser = Callable[[str], FieldValue]
SectionUpdater = Callable[[RuntimeSettings, str, FieldValue], RuntimeSettings]


@dataclass(frozen=True, slots=True)
class ConfigPatchCheck:
    valid: bool
    errors: tuple[str, ...]
    restart_required: bool
    restart_paths: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RuntimePatchSpec:
    section: str
    field: str
    parser: ValueParser


def _parse_bool(value: str) -> bool:
    return value.lower() == "true"


def _with_risk_field(
    settings: RuntimeSettings,
    field: str,
    value: FieldValue,
) -> RuntimeSettings:
    return settings.model_copy(update={"risk": settings.risk.model_copy(update={field: value})})


def _with_backtest_field(
    settings: RuntimeSettings,
    field: str,
    value: FieldValue,
) -> RuntimeSettings:
    return settings.model_copy(
        update={"backtest": settings.backtest.model_copy(update={field: value})},
    )


def _with_ui_field(
    settings: RuntimeSettings,
    field: str,
    value: FieldValue,
) -> RuntimeSettings:
    return settings.model_copy(update={"ui": settings.ui.model_copy(update={field: value})})


def _with_logging_field(
    settings: RuntimeSettings,
    field: str,
    value: FieldValue,
) -> RuntimeSettings:
    return settings.model_copy(
        update={"logging": settings.logging.model_copy(update={field: value})},
    )


def _with_notifications_field(
    settings: RuntimeSettings,
    field: str,
    value: FieldValue,
) -> RuntimeSettings:
    return settings.model_copy(
        update={"notifications": settings.notifications.model_copy(update={field: value})},
    )


RUNTIME_PATCH_SPECS: Final = {
    "risk.stake_usdt": RuntimePatchSpec("risk", "stake_usdt", Decimal),
    "risk.max_daily_loss_pct": RuntimePatchSpec("risk", "max_daily_loss_pct", Decimal),
    "risk.leverage": RuntimePatchSpec("risk", "leverage", Decimal),
    "risk.max_leverage": RuntimePatchSpec("risk", "max_leverage", Decimal),
    "risk.liquidation_buffer": RuntimePatchSpec("risk", "liquidation_buffer", Decimal),
    "risk.max_open_trades": RuntimePatchSpec("risk", "max_open_trades", int),
    "risk.stoploss_pct": RuntimePatchSpec("risk", "stoploss_pct", Decimal),
    "risk.minimal_roi": RuntimePatchSpec("risk", "minimal_roi", Decimal),
    "risk.cooldown_seconds": RuntimePatchSpec("risk", "cooldown_seconds", int),
    "risk.locked_pairs": RuntimePatchSpec("risk", "locked_pairs", str),
    "backtest.stoploss_pct": RuntimePatchSpec("backtest", "stoploss_pct", Decimal),
    "backtest.fee_rate": RuntimePatchSpec("backtest", "fee_rate", Decimal),
    "backtest.slippage_rate": RuntimePatchSpec("backtest", "slippage_rate", Decimal),
    "backtest.max_open_trades": RuntimePatchSpec("backtest", "max_open_trades", int),
    "ui.locale": RuntimePatchSpec("ui", "locale", Locale),
    "ui.read_only": RuntimePatchSpec("ui", "read_only", _parse_bool),
    "logging.level": RuntimePatchSpec("logging", "level", LogLevel),
    "notifications.enabled": RuntimePatchSpec("notifications", "enabled", _parse_bool),
    "notifications.jsonl_path": RuntimePatchSpec("notifications", "jsonl_path", str),
    "notifications.timeout_seconds": RuntimePatchSpec(
        "notifications",
        "timeout_seconds",
        Decimal,
    ),
    "notifications.max_attempts": RuntimePatchSpec("notifications", "max_attempts", int),
}
SECTION_UPDATERS: Final[dict[str, SectionUpdater]] = {
    "risk": _with_risk_field,
    "backtest": _with_backtest_field,
    "ui": _with_ui_field,
    "logging": _with_logging_field,
    "notifications": _with_notifications_field,
}


def check_config_patch(fields: tuple[ConfigFieldPatch, ...]) -> ConfigPatchCheck:
    errors: list[str] = []
    restart_paths: list[str] = []
    for field in fields:
        metadata = _metadata_for(field.path)
        if metadata is None:
            errors.append(f"{field.path} is not a known frontend setting")
            continue
        if metadata.restart_required:
            restart_paths.append(field.path)
        errors.extend(_metadata_errors(field=field, metadata=metadata))
        errors.extend(_value_errors(field))
    return ConfigPatchCheck(
        valid=len(errors) == 0,
        errors=tuple(errors),
        restart_required=len(restart_paths) > 0,
        restart_paths=tuple(restart_paths),
    )


def apply_runtime_config_patch(
    settings: RuntimeSettings,
    fields: tuple[ConfigFieldPatch, ...],
) -> RuntimeSettings:
    updated = settings
    for field in fields:
        spec = RUNTIME_PATCH_SPECS.get(field.path)
        if spec is None:
            continue
        updated = SECTION_UPDATERS[spec.section](
            updated,
            spec.field,
            spec.parser(field.value),
        )
    return updated


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
    grouped_errors = _grouped_value_errors(field)
    if grouped_errors is not None:
        return grouped_errors
    return _single_value_errors(field)


def _grouped_value_errors(field: ConfigFieldPatch) -> tuple[str, ...] | None:
    if field.path in POSITIVE_INT_FIELDS:
        return _positive_int_errors(field)
    if field.path in POSITIVE_DECIMAL_FIELDS:
        return _positive_decimal_errors(field)
    if field.path in BOOLEAN_FIELDS:
        return _boolean_errors(field)
    return None


def _single_value_errors(field: ConfigFieldPatch) -> tuple[str, ...]:
    if field.path == "notifications.max_attempts":
        return _min_int_errors(field, minimum=1)
    if field.path == "ui.locale":
        return _locale_errors(field)
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


def _locale_errors(field: ConfigFieldPatch) -> tuple[str, ...]:
    if field.value in LOCALE_VALUES:
        return ()
    return (f"{field.path} must be en, ko, or el",)


def _log_level_errors(field: ConfigFieldPatch) -> tuple[str, ...]:
    if field.value in {level.value for level in LogLevel}:
        return ()
    return (f"{field.path} must be DEBUG, INFO, WARNING, or ERROR",)
