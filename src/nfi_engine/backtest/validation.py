from __future__ import annotations

from decimal import Decimal
from typing import assert_never

from nfi_engine.backtest.errors import BacktestError, BacktestErrorCode
from nfi_engine.backtest.models import BacktestRequest, SimulationSettings
from nfi_engine.domain import TradingMode


def validate_request(request: BacktestRequest) -> None:
    if len(request.candles.candles) == 0:
        raise BacktestError(
            code=BacktestErrorCode.BACKTEST_NO_CANDLES,
            message="backtest requires at least one candle",
        )
    request.candles.pair.require_mode(request.settings.trading_mode)
    validate_liquidation_buffer(request.settings)


def validate_liquidation_buffer(settings: SimulationSettings) -> None:
    match settings.trading_mode:
        case TradingMode.SPOT:
            return
        case TradingMode.FUTURES:
            safe_stoploss = (Decimal(1) / settings.leverage) - settings.liquidation_buffer
            if settings.stoploss_pct >= safe_stoploss:
                raise BacktestError(
                    code=BacktestErrorCode.LIQUIDATION_BUFFER_VIOLATION,
                    message="stoploss is inside or beyond the configured liquidation buffer",
                )
        case unreachable:
            assert_never(unreachable)
