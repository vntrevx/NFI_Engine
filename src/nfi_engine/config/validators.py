from __future__ import annotations

from pathlib import Path
from typing import assert_never

from nfi_engine.config.enums import ConfigErrorCode
from nfi_engine.config.errors import ConfigLoadError
from nfi_engine.config.models import RuntimeSettings
from nfi_engine.domain import DomainError, Leverage, LiquidationBuffer, MarginMode, TradingMode
from nfi_engine.exchange.capabilities import get_exchange_profile
from nfi_engine.exchange.credential_requirements import missing_runtime_credential_fields


def validate_runtime_settings_model(*, settings: RuntimeSettings, path: Path) -> None:
    _validate_trading_mode(settings=settings, path=path)
    _validate_exchange_capability(settings=settings, path=path)
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


def _validate_exchange_capability(*, settings: RuntimeSettings, path: Path) -> None:
    profile = get_exchange_profile(settings.exchange.name)
    if profile is None:
        raise ConfigLoadError(
            code=ConfigErrorCode.EXCHANGE_UNSUPPORTED,
            message=f"unsupported exchange: {settings.exchange.name}",
            path=path,
        )
    if not profile.supports_trading_mode(settings.exchange.trading_mode):
        raise ConfigLoadError(
            code=ConfigErrorCode.EXCHANGE_TRADING_MODE_UNSUPPORTED,
            message=(
                f"{profile.exchange_id} does not support "
                f"{settings.exchange.trading_mode.value} in registry"
            ),
            path=path,
        )
    margin_mode = settings.exchange.margin_mode
    if margin_mode is not None and not profile.supports_margin_mode(margin_mode):
        raise ConfigLoadError(
            code=ConfigErrorCode.EXCHANGE_MARGIN_MODE_UNSUPPORTED,
            message=f"{profile.exchange_id} does not support {margin_mode.value} margin",
            path=path,
        )


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
    missing_credentials = missing_runtime_credential_fields(settings)
    if missing_credentials:
        raise ConfigLoadError(
            code=ConfigErrorCode.MISSING_EXCHANGE_KEY,
            message=(
                f"live_trading requires exchange credential fields: {','.join(missing_credentials)}"
            ),
            path=path,
        )
