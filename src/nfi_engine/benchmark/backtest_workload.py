from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Final

from nfi_engine.backtest import (
    BacktestRequest,
    ReproducibilityMetadata,
    SimulationSettings,
    run_backtest,
)
from nfi_engine.data import CandleBatch
from nfi_engine.domain import Candle, Price, Quantity, TradingMode, TradingPair
from nfi_engine.strategy import FreqtradeStrategyAdapter
from nfi_engine.strategy.demo import AdapterSmokeStrategy

BACKTEST_WORKLOAD_CANDLES: Final = 720
BACKTEST_WORKLOAD_TIMEFRAME: Final = "5m"
ONE: Final = Decimal(1)
ONE_HUNDRED: Final = Decimal(100)
ONE_THOUSAND: Final = Decimal(1000)


def build_backtest_workload_request() -> BacktestRequest:
    strategy = AdapterSmokeStrategy()
    return BacktestRequest(
        candles=_batch(),
        adapter=FreqtradeStrategyAdapter.from_strategy(strategy),
        settings=SimulationSettings(
            trading_mode=TradingMode.SPOT,
            starting_balance=ONE_THOUSAND,
            stake_amount=Decimal(10),
            fee_rate=Decimal(0),
            slippage_rate=Decimal(0),
            max_open_trades=1,
            leverage=ONE,
            liquidation_buffer=Decimal("0.05"),
            stoploss_pct=Decimal("0.10"),
        ),
        config_digest="benchmark-digest",
        strategy_name=type(strategy).__name__,
        metadata=_metadata(),
    )


def run_backtest_workload(request: BacktestRequest) -> int:
    return len(run_backtest(request).equity_curve)


def _batch() -> CandleBatch:
    pair = TradingPair.parse("BTC/USDT", TradingMode.SPOT)
    started_at = datetime(2026, 1, 1, tzinfo=UTC)
    candles = tuple(
        Candle(
            pair=pair,
            opened_at=started_at + timedelta(minutes=index * 5),
            open=Price(ONE_HUNDRED),
            high=Price(ONE_HUNDRED),
            low=Price(ONE_HUNDRED),
            close=Price(ONE_HUNDRED),
            volume=Quantity(ONE),
        )
        for index in range(BACKTEST_WORKLOAD_CANDLES)
    )
    return CandleBatch(pair=pair, timeframe=BACKTEST_WORKLOAD_TIMEFRAME, candles=candles)


def _metadata() -> ReproducibilityMetadata:
    return ReproducibilityMetadata(
        config_hash="benchmark-digest",
        strategy_hash="adapter-smoke-strategy",
        data_hash=f"synthetic-{BACKTEST_WORKLOAD_CANDLES}-flat-candles",
        engine_version="0.1.0",
        git_commit=None,
        dependency_lock_hash="benchmark-lock",
        python_version="3.12.0",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        command_args=("benchmark", "m2", "backtest-workload"),
    )
