from __future__ import annotations

from html import escape
from typing import Final, assert_never

from nfi_engine.config import FieldGroup, FieldMetadata, Locale, RuntimeSettings, frontend_metadata
from nfi_engine.ui.i18n import localize
from nfi_engine.ui.i18n_keys import MessageKey
from nfi_engine.ui.settings_exchange import render_exchange_select
from nfi_engine.ui.settings_field_values import field_value

NUMERIC_FIELDS: Final = frozenset(
    (
        "risk.stake_usdt",
        "risk.allocation_cap_pct",
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
BOOLEAN_FIELDS: Final = frozenset(
    ("risk.expert_risk_confirmed", "ui.read_only", "notifications.enabled")
)
PERMISSION_FIELDS: Final = frozenset(
    (
        "exchange.permission_read",
        "exchange.permission_trade",
        "exchange.permission_futures",
        "exchange.permission_withdrawal",
        "exchange.permission_ip_allowlist",
    )
)
FIXED_SELECT_OPTIONS: Final[dict[str, tuple[str, ...]]] = {
    "exchange.trading_mode": ("spot", "futures"),
    "risk.risk_profile": ("safe", "balanced", "expert"),
    "logging.level": ("DEBUG", "INFO", "WARNING", "ERROR"),
}
OPTION_LABELS: Final[dict[str, MessageKey]] = {
    "aggressive": MessageKey.SETUP_OPTION_AGGRESSIVE,
    "balanced": MessageKey.SETUP_OPTION_BALANCED,
    "conservative": MessageKey.SETUP_OPTION_CONSERVATIVE,
    "disabled": MessageKey.SETUP_OPTION_DISABLED,
    "enabled": MessageKey.SETUP_OPTION_ENABLED,
    "expert": MessageKey.SETUP_OPTION_EXPERT,
    "futures": MessageKey.SETUP_OPTION_FUTURES,
    "not_applicable": MessageKey.SETUP_OPTION_NOT_APPLICABLE,
    "safe": MessageKey.SETUP_OPTION_SAFE,
    "spot": MessageKey.SETUP_OPTION_SPOT,
    "unknown": MessageKey.SETUP_OPTION_UNKNOWN,
}
SIMPLE_FIELD_ORDER: Final = (
    "exchange.name",
    "exchange.trading_mode",
    "ui.locale",
    "risk.stake_usdt",
    "risk.max_open_trades",
)
SAFETY_FIELD_PATHS: Final = frozenset(("risk.risk_profile", "risk.expert_risk_confirmed"))


def render_settings_fields(settings: RuntimeSettings) -> str:
    locale = settings.ui.locale
    simple = "\n".join(
        _field_row(settings=settings, field=field, locale=locale) for field in _simple_fields()
    )
    advanced = "\n".join(
        _field_row(settings=settings, field=field, locale=locale) for field in _advanced_fields()
    )
    return (
        '<div data-testid="simple-settings" class="settings-group settings-simple-group">\n'
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
    hidden_paths = simple_paths | SAFETY_FIELD_PATHS
    return tuple(
        field
        for field in _visible_fields()
        if field.ui_group is FieldGroup.ADVANCED and field.path not in hidden_paths
    )


def _field_row(*, settings: RuntimeSettings, field: FieldMetadata, locale: Locale) -> str:
    value = field_value(settings=settings, path=field.path)
    note = localize(
        locale,
        MessageKey.SETTINGS_RUNTIME_SAFE
        if field.runtime_apply_safe
        else MessageKey.SETTINGS_RELOAD_REQUIRED,
    )
    return f"""
<div class="field-row">
  <label for="{escape(field.path)}">{escape(_field_label(field.path, locale=locale))}</label>
  {_control(field=field, value=value, locale=locale)}
  <span class="field-note">{note}</span>
</div>
"""


def _control(*, field: FieldMetadata, value: str, locale: Locale) -> str:
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
    select_control = _select_control(
        field=field,
        value=value,
        common=common,
        disabled=disabled,
        locale=locale,
    )
    if select_control is not None:
        return select_control
    if field.path in NUMERIC_FIELDS:
        step = "1" if field.path.endswith(("trades", "seconds", "attempts")) else "0.01"
        min_value = "1" if field.path.endswith(("trades", "attempts")) else "0"
        return (
            f'<input type="number" min="{min_value}" step="{step}" '
            f'value="{escape(value)}" {common}>'
        )
    return f'<input type="text" value="{escape(value)}" {common}{disabled}>'


def _select_control(
    *,
    field: FieldMetadata,
    value: str,
    common: str,
    disabled: str,
    locale: Locale,
) -> str | None:
    if field.path == "exchange.name":
        return render_exchange_select(
            common=common,
            value=value,
            disabled=disabled,
            locale=locale,
        )
    fixed_options = FIXED_SELECT_OPTIONS.get(field.path)
    if fixed_options is not None:
        fixed_disabled = disabled if field.path == "exchange.trading_mode" else ""
        return _select(
            common=common,
            value=value,
            options=fixed_options,
            disabled=fixed_disabled,
            locale=locale,
        )
    if field.path in PERMISSION_FIELDS:
        return _select(
            common=common,
            value=value,
            options=("unknown", "enabled", "disabled", "not_applicable"),
            disabled=disabled,
            locale=locale,
        )
    if field.path == "ui.locale":
        return _locale_select(common=common, value=value)
    return None


def _select(
    *,
    common: str,
    value: str,
    options: tuple[str, ...],
    locale: Locale,
    disabled: str = "",
) -> str:
    choices = "\n".join(_option(value=value, option=option, locale=locale) for option in options)
    return f"<select {common}{disabled}>{choices}</select>"


def _locale_select(*, common: str, value: str) -> str:
    choices = "\n".join(_locale_option(value=value, locale=locale) for locale in Locale)
    return f"<select {common}>{choices}</select>"


def _option(*, value: str, option: str, locale: Locale) -> str:
    selected = " selected" if value == option else ""
    label_key = OPTION_LABELS.get(option)
    label = option.title() if label_key is None else localize(locale, label_key)
    return f'<option value="{escape(option)}"{selected}>{escape(label)}</option>'


def _locale_option(*, value: str, locale: Locale) -> str:
    selected = " selected" if value == locale.value else ""
    return (
        f'<option value="{escape(locale.value)}"{selected}>{escape(_locale_label(locale))}</option>'
    )


def _locale_label(locale: Locale) -> str:
    match locale:
        case Locale.EN:
            return "English"
        case Locale.KO:
            return "한국어"
        case Locale.EL:
            return "Ελληνικά"
        case unreachable:
            assert_never(unreachable)


def _field_label(path: str, *, locale: Locale) -> str:
    labels: dict[str, MessageKey] = {
        "exchange.name": MessageKey.FIELD_EXCHANGE_NAME,
        "exchange.trading_mode": MessageKey.FIELD_TRADING_MODE,
        "exchange.permission_withdrawal": MessageKey.FIELD_PERMISSION_WITHDRAWAL,
        "ui.locale": MessageKey.FIELD_UI_LOCALE,
        "risk.risk_profile": MessageKey.FIELD_RISK_PROFILE,
        "risk.expert_risk_confirmed": MessageKey.FIELD_EXPERT_RISK_CONFIRMED,
        "risk.stake_usdt": MessageKey.FIELD_RISK_STAKE,
        "risk.max_open_trades": MessageKey.FIELD_MAX_OPEN_TRADES,
    }
    if path in labels:
        return localize(locale, labels[path])
    return path.replace("_", " ").replace(".", " / ").title()
