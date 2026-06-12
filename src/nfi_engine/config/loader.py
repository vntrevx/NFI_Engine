from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Final, assert_never

from pydantic import ValidationError

from nfi_engine.config.enums import ConfigErrorCode
from nfi_engine.config.errors import ConfigLoadError
from nfi_engine.config.models import RuntimeSettings
from nfi_engine.domain import DomainError, Leverage, LiquidationBuffer, MarginMode, TradingMode

type ConfigScalar = str | int | float | bool | None
type ConfigValue = ConfigScalar | list[ConfigValue] | dict[str, ConfigValue]
type ConfigData = dict[str, ConfigValue]

ENV_OVERRIDES: Final = (
    ("NFI_ENGINE__ENGINE__LIVE_TRADING", ("engine", "live_trading")),
    ("NFI_ENGINE__ENGINE__LIVE_TRADING_CONFIRMED", ("engine", "live_trading_confirmed")),
    ("NFI_ENGINE__EXCHANGE__API_KEY", ("exchange", "api_key")),
    ("NFI_ENGINE__EXCHANGE__API_SECRET", ("exchange", "api_secret")),
    ("NFI_ENGINE__EXCHANGE__TRADING_MODE", ("exchange", "trading_mode")),
    ("NFI_ENGINE__EXCHANGE__MARGIN_MODE", ("exchange", "margin_mode")),
    ("NFI_ENGINE__RISK__STAKE_USDT", ("risk", "stake_usdt")),
    ("NFI_ENGINE__RISK__LEVERAGE", ("risk", "leverage")),
    ("NFI_ENGINE__RISK__MAX_LEVERAGE", ("risk", "max_leverage")),
    ("NFI_ENGINE__RISK__MAX_OPEN_TRADES", ("risk", "max_open_trades")),
    ("NFI_ENGINE__RISK__LIQUIDATION_BUFFER", ("risk", "liquidation_buffer")),
    ("NFI_ENGINE__API__AUTH_TOKEN", ("api", "auth_token")),
    ("NFI_ENGINE__LOGGING__LEVEL", ("logging", "level")),
)
MIN_QUOTED_SCALAR_LENGTH: Final = 2


def load_runtime_settings(path: Path) -> RuntimeSettings:
    raw_config = _read_yaml_config(path)
    config_with_env = _apply_env_overrides(raw_config, os.environ)
    try:
        settings = RuntimeSettings.model_validate(config_with_env)
    except ValidationError as exc:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message=_format_validation_error(exc),
            path=path,
        ) from exc
    validate_runtime_settings(settings=settings, path=path)
    return settings


def validate_runtime_settings(*, settings: RuntimeSettings, path: Path) -> None:
    _validate_runtime_settings(settings=settings, path=path)


def _read_yaml_config(path: Path) -> ConfigData:
    if not path.exists():
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_FILE_NOT_FOUND,
            message="config file does not exist",
            path=path,
        )
    return _parse_yaml_mapping(path.read_text(encoding="utf-8").splitlines(), path)


def _parse_yaml_mapping(lines: Iterable[str], path: Path) -> ConfigData:
    root: ConfigData = {}
    stack: list[tuple[int, ConfigData]] = [(-1, root)]
    for line_number, line in enumerate(lines, start=1):
        if _is_ignored_yaml_line(line):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise _yaml_error(
                path=path, line_number=line_number, message="indent must use two spaces"
            )
        key, raw_value = _parse_yaml_line(line=line, path=path, line_number=line_number)
        while indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if raw_value is None:
            nested: ConfigData = {}
            parent[key] = nested
            stack.append((indent, nested))
        else:
            parent[key] = _parse_scalar(raw_value)
    return root


def _is_ignored_yaml_line(line: str) -> bool:
    stripped = line.strip()
    return stripped == "" or stripped.startswith("#")


def _parse_yaml_line(*, line: str, path: Path, line_number: int) -> tuple[str, str | None]:
    stripped = line.strip()
    key, separator, value = stripped.partition(":")
    if separator == "" or key == "":
        raise _yaml_error(path=path, line_number=line_number, message="expected key: value")
    normalized_value = value.strip()
    if normalized_value == "":
        return key, None
    return key, normalized_value


def _parse_scalar(raw: str) -> ConfigScalar:
    unquoted = _unquote(raw)
    match unquoted.lower():
        case "null" | "~":
            return None
        case "true":
            return True
        case "false":
            return False
        case _:
            return unquoted


def _unquote(raw: str) -> str:
    if len(raw) >= MIN_QUOTED_SCALAR_LENGTH and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    return raw


def _yaml_error(*, path: Path, line_number: int, message: str) -> ConfigLoadError:
    return ConfigLoadError(
        code=ConfigErrorCode.YAML_NOT_MAPPING,
        message=f"{message} at line {line_number}",
        path=path,
    )


def _apply_env_overrides(config: ConfigData, environ: Mapping[str, str]) -> ConfigData:
    current = _clone_config(config)
    for env_name, path in ENV_OVERRIDES:
        env_value = environ.get(env_name)
        if env_value is not None:
            current = _with_nested_override(current, path, env_value)
    return current


def _with_nested_override(config: ConfigData, path: tuple[str, str], value: str) -> ConfigData:
    section, key = path
    current = _clone_config(config)
    section_value = current.get(section)
    nested: ConfigData = section_value if isinstance(section_value, dict) else {}
    nested[key] = value
    current[section] = nested
    return current


def _clone_config(config: ConfigData) -> ConfigData:
    return {key: _clone_value(value) for key, value in config.items()}


def _clone_value(value: ConfigValue) -> ConfigValue:
    match value:
        case dict():
            return {key: _clone_value(child) for key, child in value.items()}
        case list():
            return [_clone_value(child) for child in value]
        case str() | int() | float() | bool() | None:
            return value
        case unreachable:
            assert_never(unreachable)


def _validate_runtime_settings(*, settings: RuntimeSettings, path: Path) -> None:
    _validate_trading_mode(settings=settings, path=path)
    _validate_risk_settings(settings=settings, path=path)
    _validate_backtest_settings(settings=settings, path=path)
    _validate_notification_settings(settings=settings, path=path)
    if settings.engine.live_trading:
        _validate_live_trading(settings=settings, path=path)


def _validate_trading_mode(*, settings: RuntimeSettings, path: Path) -> None:
    match settings.exchange.trading_mode:
        case TradingMode.SPOT:
            if settings.exchange.margin_mode is not None:
                raise ConfigLoadError(
                    code=ConfigErrorCode.SPOT_MARGIN_MODE_NOT_ALLOWED,
                    message="spot config must not set margin_mode",
                    path=path,
                )
        case TradingMode.FUTURES:
            match settings.exchange.margin_mode:
                case MarginMode.ISOLATED | MarginMode.CROSS:
                    return
                case None:
                    raise ConfigLoadError(
                        code=ConfigErrorCode.FUTURES_MARGIN_MODE_REQUIRED,
                        message="futures config requires margin_mode isolated or cross",
                        path=path,
                    )
                case unreachable:
                    assert_never(unreachable)
        case unreachable:
            assert_never(unreachable)


def _validate_risk_settings(*, settings: RuntimeSettings, path: Path) -> None:
    try:
        Leverage.parse(str(settings.risk.leverage))
        Leverage.parse(str(settings.risk.max_leverage))
        LiquidationBuffer.parse(str(settings.risk.liquidation_buffer))
    except DomainError as exc:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message=str(exc),
            path=path,
        ) from exc
    if settings.risk.max_open_trades < 1:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message="risk.max_open_trades must be at least 1",
            path=path,
        )
    if settings.risk.stoploss_pct <= 0 or settings.risk.stoploss_pct >= 1:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message="risk.stoploss_pct must be greater than 0 and less than 1",
            path=path,
        )
    if settings.risk.minimal_roi < 0:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message="risk.minimal_roi must be greater than or equal to 0",
            path=path,
        )
    if settings.risk.cooldown_seconds < 0:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message="risk.cooldown_seconds must be greater than or equal to 0",
            path=path,
        )


def _validate_backtest_settings(*, settings: RuntimeSettings, path: Path) -> None:
    if settings.backtest.stoploss_pct <= 0 or settings.backtest.stoploss_pct >= 1:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message="backtest.stoploss_pct must be greater than 0 and less than 1",
            path=path,
        )
    if settings.backtest.fee_rate < 0 or settings.backtest.fee_rate >= 1:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message="backtest.fee_rate must be greater than or equal to 0 and less than 1",
            path=path,
        )
    if settings.backtest.slippage_rate < 0 or settings.backtest.slippage_rate >= 1:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message="backtest.slippage_rate must be greater than or equal to 0 and less than 1",
            path=path,
        )
    if settings.backtest.max_open_trades < 0:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message="backtest.max_open_trades must be greater than or equal to 0",
            path=path,
        )


def _validate_notification_settings(*, settings: RuntimeSettings, path: Path) -> None:
    if settings.notifications.timeout_seconds <= 0:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message="notifications.timeout_seconds must be greater than 0",
            path=path,
        )
    if settings.notifications.max_attempts < 1:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message="notifications.max_attempts must be at least 1",
            path=path,
        )


def _validate_live_trading(*, settings: RuntimeSettings, path: Path) -> None:
    if not settings.engine.live_trading_confirmed:
        raise ConfigLoadError(
            code=ConfigErrorCode.LIVE_TRADING_REQUIRES_CONFIRMATION,
            message="live_trading requires live_trading_confirmed=true",
            path=path,
        )
    if not settings.exchange.api_key or not settings.exchange.api_secret:
        raise ConfigLoadError(
            code=ConfigErrorCode.MISSING_EXCHANGE_KEY,
            message="live_trading requires exchange api_key and api_secret",
            path=path,
        )


def _format_validation_error(exc: ValidationError) -> str:
    return "; ".join(error["type"] for error in exc.errors())
