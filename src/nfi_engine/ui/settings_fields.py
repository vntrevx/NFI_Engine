from __future__ import annotations

from decimal import Decimal
from html import escape
from typing import Final

from nfi_engine.config import FieldGroup, FieldMetadata, Locale, RuntimeSettings, frontend_metadata
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey

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
SIMPLE_FIELD_ORDER: Final = (
    "exchange.name",
    "exchange.trading_mode",
    "ui.locale",
    "risk.stake_usdt",
    "risk.max_open_trades",
)


def render_settings_fields(settings: RuntimeSettings) -> str:
    locale = settings.ui.locale
    simple = "\n".join(
        _field_row(settings=settings, field=field, locale=locale) for field in _simple_fields()
    )
    advanced = "\n".join(
        _field_row(settings=settings, field=field, locale=locale) for field in _advanced_fields()
    )
    return (
        '<div data-testid="simple-settings" class="settings-group">\n'
        f"  <h2>{localize(locale, MessageKey.SETTINGS_SIMPLE_MODE)}</h2>\n"
        f'  <p class="muted">{localize(locale, MessageKey.SETTINGS_SIMPLE_HELP)}</p>\n'
        f'  <div class="field-grid">\n{simple}\n  </div>\n'
        "</div>\n"
        '<details data-testid="advanced-settings" class="settings-group">\n'
        f"  <summary>{localize(locale, MessageKey.SETTINGS_ADVANCED)}</summary>\n"
        f'  <div class="field-grid">\n{advanced}\n  </div>\n'
        "</details>\n"
    )


def _visible_fields() -> tuple[FieldMetadata, ...]:
    return tuple(
        field for field in frontend_metadata() if field.frontend_editable and not field.sensitive
    )


def _simple_fields() -> tuple[FieldMetadata, ...]:
    fields = {field.path: field for field in _visible_fields()}
    return tuple(fields[path] for path in SIMPLE_FIELD_ORDER if path in fields)


def _advanced_fields() -> tuple[FieldMetadata, ...]:
    simple_paths = frozenset(SIMPLE_FIELD_ORDER)
    return tuple(
        field
        for field in _visible_fields()
        if field.ui_group is FieldGroup.ADVANCED and field.path not in simple_paths
    )


def _field_row(*, settings: RuntimeSettings, field: FieldMetadata, locale: Locale) -> str:
    value = _field_value(settings=settings, path=field.path)
    note = localize(
        locale,
        MessageKey.SETTINGS_RUNTIME_SAFE
        if field.runtime_apply_safe
        else MessageKey.SETTINGS_RELOAD_REQUIRED,
    )
    return f"""
<div class="field-row">
  <label for="{escape(field.path)}">{escape(_field_label(field.path, locale=locale))}</label>
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
    if field.path == "exchange.trading_mode":
        return _select(common=common, value=value, options=("spot", "futures"), disabled=disabled)
    if field.path == "ui.locale":
        return _select(common=common, value=value, options=tuple(locale.value for locale in Locale))
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


def _select(*, common: str, value: str, options: tuple[str, ...], disabled: str = "") -> str:
    choices = "\n".join(_option(value=value, option=option) for option in options)
    return f"<select {common}{disabled}>{choices}</select>"


def _option(*, value: str, option: str) -> str:
    selected = " selected" if value == option else ""
    return f'<option value="{escape(option)}"{selected}>{escape(option.title())}</option>'


def _field_label(path: str, *, locale: Locale) -> str:
    labels: dict[str, MessageKey] = {
        "exchange.name": MessageKey.FIELD_EXCHANGE_NAME,
        "exchange.trading_mode": MessageKey.FIELD_TRADING_MODE,
        "ui.locale": MessageKey.FIELD_UI_LOCALE,
        "risk.stake_usdt": MessageKey.FIELD_RISK_STAKE,
        "risk.max_open_trades": MessageKey.FIELD_MAX_OPEN_TRADES,
    }
    if path in labels:
        return localize(locale, labels[path])
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
