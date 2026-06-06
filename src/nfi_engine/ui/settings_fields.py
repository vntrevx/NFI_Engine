from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import Final

from nfi_engine.config import FieldMetadata, RuntimeSettings, frontend_metadata

NUMERIC_FIELDS: Final = frozenset(
    (
        "risk.stake_usdt",
        "risk.max_daily_loss_pct",
        "risk.leverage",
        "risk.max_leverage",
        "risk.liquidation_buffer",
        "risk.max_open_trades",
        "risk.stoploss_pct",
        "risk.minimal_roi",
        "risk.cooldown_seconds",
        "backtest.stoploss_pct",
        "backtest.fee_rate",
        "backtest.slippage_rate",
        "backtest.max_open_trades",
        "notifications.timeout_seconds",
        "notifications.max_attempts",
    ),
)
BOOLEAN_FIELDS: Final = frozenset(("ui.read_only", "notifications.enabled"))


def render_settings_fields(settings: RuntimeSettings) -> str:
    return "\n".join(_field_row(settings=settings, field=field) for field in _visible_fields())


def _visible_fields() -> tuple[FieldMetadata, ...]:
    return tuple(
        field for field in frontend_metadata() if field.frontend_editable and not field.sensitive
    )


def _field_row(*, settings: RuntimeSettings, field: FieldMetadata) -> str:
    value = _field_value(settings=settings, path=field.path)
    note = "Runtime safe" if field.runtime_apply_safe else "Reload required"
    return f"""
<div class="field-row">
  <label for="{escape(field.path)}">{escape(_field_label(field.path))}</label>
  {_control(field=field, value=value)}
  <span class="field-note">{note}</span>
</div>
"""


def _control(*, field: FieldMetadata, value: str) -> str:
    escaped_path = escape(field.path)
    common = (
        f'id="{escaped_path}" name="{escaped_path}" '
        f'data-testid="field-{escaped_path}" '
        f'data-runtime-safe="{str(field.runtime_apply_safe).lower()}"'
    )
    disabled = "" if field.runtime_apply_safe else " disabled"
    if field.path in BOOLEAN_FIELDS:
        checked = " checked" if value == "true" else ""
        return f'<input type="checkbox" {common}{checked}{disabled}>'
    if field.path == "logging.level":
        return _select(common=common, value=value, options=("DEBUG", "INFO", "WARNING", "ERROR"))
    if field.path in NUMERIC_FIELDS:
        step = "1" if field.path.endswith(("trades", "seconds", "attempts")) else "0.01"
        min_value = "1" if field.path.endswith(("trades", "attempts")) else "0"
        return (
            f'<input type="number" min="{min_value}" step="{step}" '
            f'value="{escape(value)}" {common}>'
        )
    return f'<input type="text" value="{escape(value)}" {common}{disabled}>'


def _select(*, common: str, value: str, options: tuple[str, ...]) -> str:
    choices = "\n".join(_option(value=value, option=option) for option in options)
    return f"<select {common}>{choices}</select>"


def _option(*, value: str, option: str) -> str:
    selected = " selected" if value == option else ""
    return f'<option value="{escape(option)}"{selected}>{escape(option.title())}</option>'


def _field_label(path: str) -> str:
    return path.replace("_", " ").replace(".", " / ").title()


def _field_value(*, settings: RuntimeSettings, path: str) -> str:
    return _field_values(settings).get(path, "")


def _field_values(settings: RuntimeSettings) -> dict[str, str]:
    margin_mode = (
        "" if settings.exchange.margin_mode is None else settings.exchange.margin_mode.value
    )
    return {
        "exchange.name": settings.exchange.name,
        "exchange.trading_mode": settings.exchange.trading_mode.value,
        "exchange.margin_mode": margin_mode,
        "risk.stake_usdt": _decimal(settings.risk.stake_usdt),
        "risk.max_daily_loss_pct": _decimal(settings.risk.max_daily_loss_pct),
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
