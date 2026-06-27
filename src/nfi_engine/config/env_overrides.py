from __future__ import annotations

from collections.abc import Mapping
from typing import Final, assert_never

type ConfigScalar = str | int | float | bool | None
type ConfigValue = ConfigScalar | list[ConfigValue] | dict[str, ConfigValue]
type ConfigData = dict[str, ConfigValue]

ENV_OVERRIDES: Final = (
    ("NFI_ENGINE__ENGINE__LIVE_TRADING", ("engine", "live_trading")),
    ("NFI_ENGINE__ENGINE__LIVE_TRADING_CONFIRMED", ("engine", "live_trading_confirmed")),
    ("NFI_ENGINE__EXCHANGE__API_KEY", ("exchange", "api_key")),
    ("NFI_ENGINE__EXCHANGE__API_SECRET", ("exchange", "api_secret")),
    ("NFI_ENGINE__EXCHANGE__PASSPHRASE", ("exchange", "passphrase")),
    ("NFI_ENGINE__EXCHANGE__MEMO", ("exchange", "memo")),
    ("NFI_ENGINE__EXCHANGE__OPERATOR_ID", ("exchange", "operator_id")),
    ("NFI_ENGINE__EXCHANGE__ACCOUNT_ADDRESS", ("exchange", "account_address")),
    ("NFI_ENGINE__EXCHANGE__API_WALLET_SIGNER", ("exchange", "api_wallet_signer")),
    ("NFI_ENGINE__EXCHANGE__TRADING_MODE", ("exchange", "trading_mode")),
    ("NFI_ENGINE__EXCHANGE__MARGIN_MODE", ("exchange", "margin_mode")),
    ("NFI_ENGINE__RISK__STAKE_USDT", ("risk", "stake_usdt")),
    ("NFI_ENGINE__RISK__LEVERAGE", ("risk", "leverage")),
    ("NFI_ENGINE__RISK__MAX_LEVERAGE", ("risk", "max_leverage")),
    ("NFI_ENGINE__RISK__MAX_OPEN_TRADES", ("risk", "max_open_trades")),
    ("NFI_ENGINE__RISK__LIQUIDATION_BUFFER", ("risk", "liquidation_buffer")),
    ("NFI_ENGINE__API__AUTH_TOKEN", ("api", "auth_token")),
    ("NFI_ENGINE__API__OPERATOR_USERNAME", ("api", "operator_username")),
    ("NFI_ENGINE__API__OPERATOR_PASSWORD", ("api", "operator_password")),
    ("NFI_ENGINE__LOGGING__LEVEL", ("logging", "level")),
)


def apply_env_overrides(config: ConfigData, environ: Mapping[str, str]) -> ConfigData:
    current = clone_config(config)
    for env_name, path in ENV_OVERRIDES:
        env_value = environ.get(env_name)
        if env_value is not None:
            _set_nested_override(current, path, env_value)
    return current


def clone_config(config: ConfigData) -> ConfigData:
    return {key: clone_value(value) for key, value in config.items()}


def clone_value(value: ConfigValue) -> ConfigValue:
    match value:
        case dict():
            return {key: clone_value(child) for key, child in value.items()}
        case list():
            return [clone_value(child) for child in value]
        case str() | int() | float() | bool() | None:
            return value
        case unreachable:
            assert_never(unreachable)


def _set_nested_override(config: ConfigData, path: tuple[str, str], value: str) -> None:
    section, key = path
    section_value = config.get(section)
    if isinstance(section_value, dict):
        nested = section_value
    else:
        nested = {}
        config[section] = nested
    nested[key] = value
