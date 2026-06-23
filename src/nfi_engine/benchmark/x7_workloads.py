from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Final

import anyio

from nfi_engine.backtest import (
    BacktestRequest,
    ReproducibilityMetadata,
    SimulationSettings,
    run_backtest,
)
from nfi_engine.backtest.frames import strategy_frame_for_cursor
from nfi_engine.config import RuntimeSettings, load_runtime_settings
from nfi_engine.data import CandleBatch
from nfi_engine.domain import (
    AccountSnapshot,
    Candle,
    Price,
    Quantity,
    StakeAmount,
    TradingMode,
    TradingPair,
)
from nfi_engine.paper import PaperRunRequest, PaperTick, run_paper
from nfi_engine.strategy import DataProviderFacade, FreqtradeStrategyAdapter, PairFrame
from nfi_engine.strategy.nfi_x7 import (
    X7FeatureGraph,
    X7FeatureGraphContext,
    X7FeatureGraphRequest,
    X7NativeStrategy,
    build_x7_semantic_status,
)

X7_CONFIG: Final = Path("examples/x7-futures-paper.yaml")
X7_PAIR: Final = TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
X7_BACKTEST_SAMPLE_CANDLES: Final = 120
X7_PAPER_SAMPLE_TICKS: Final = 24
ONE: Final = Decimal(1)
ONE_THOUSAND: Final = Decimal(1000)


def load_x7_benchmark_settings() -> RuntimeSettings:
    return load_runtime_settings(X7_CONFIG)


def inspect_x7_strategy_payload(settings: RuntimeSettings) -> int:
    strategy = X7NativeStrategy()
    inspection = FreqtradeStrategyAdapter.from_strategy(strategy).inspect()
    status = build_x7_semantic_status(settings=settings, readiness=None)
    return (
        len(inspection.detected_callbacks)
        + len(status.covered_modules)
        + len(status.pending_modules)
    )


def run_x7_feature_graph_workload() -> int:
    context = _feature_graph_context()
    result = X7FeatureGraph().build(context)
    return len(result.frame.rows) + result.coverage.total_feature_count


def run_x7_backtest_workload(settings: RuntimeSettings) -> int:
    request = BacktestRequest(
        candles=_batch(
            pair=X7_PAIR,
            timeframe="5m",
            candle_count=X7_BACKTEST_SAMPLE_CANDLES,
            step=timedelta(minutes=5),
        ),
        adapter=FreqtradeStrategyAdapter.from_strategy(X7NativeStrategy()),
        settings=SimulationSettings(
            trading_mode=TradingMode.FUTURES,
            starting_balance=ONE_THOUSAND,
            stake_amount=settings.risk.stake_usdt,
            fee_rate=settings.backtest.fee_rate,
            slippage_rate=settings.backtest.slippage_rate,
            max_open_trades=settings.backtest.max_open_trades,
            leverage=settings.risk.leverage,
            liquidation_buffer=settings.risk.liquidation_buffer,
            stoploss_pct=settings.backtest.stoploss_pct,
        ),
        config_digest="x7-benchmark-digest",
        strategy_name=X7NativeStrategy.__name__,
        metadata=_metadata(),
    )
    return len(run_backtest(request).timeline.steps)


def run_x7_paper_workload(settings: RuntimeSettings) -> int:
    with tempfile.TemporaryDirectory(prefix="nfi-x7-paper-benchmark-") as directory:
        result = anyio.run(
            run_paper,
            PaperRunRequest(
                settings=settings,
                ticks=_paper_ticks(),
                max_events=X7_PAPER_SAMPLE_TICKS,
                database_url=f"sqlite+aiosqlite:///{Path(directory) / 'paper.sqlite'}",
                strategy_adapter=FreqtradeStrategyAdapter.from_strategy(X7NativeStrategy()),
                account_snapshot=AccountSnapshot(
                    captured_at=datetime(2026, 1, 1, tzinfo=UTC),
                    equity=StakeAmount(ONE_THOUSAND),
                    available=StakeAmount(ONE_THOUSAND),
                    positions=(),
                ),
            ),
        )
    return result.processed_events + len(result.timeline.steps)


def _feature_graph_context() -> X7FeatureGraphContext:
    base = _batch(pair=X7_PAIR, timeframe="5m", candle_count=72, step=timedelta(minutes=5))
    informative_15m = _batch(
        pair=X7_PAIR,
        timeframe="15m",
        candle_count=36,
        step=timedelta(minutes=15),
    )
    informative_1h = _batch(pair=X7_PAIR, timeframe="1h", candle_count=18, step=timedelta(hours=1))
    return X7FeatureGraphContext(
        base_frame=strategy_frame_for_cursor(batch=base, visible_count=len(base.candles)),
        provider=_provider(
            base=base, informative_15m=informative_15m, informative_1h=informative_1h
        ),
        request=X7FeatureGraphRequest(
            pair=X7_PAIR,
            base_timeframe=base.timeframe,
            informative_timeframes=(informative_15m.timeframe, informative_1h.timeframe),
        ),
    )


def _provider(
    *,
    base: CandleBatch,
    informative_15m: CandleBatch,
    informative_1h: CandleBatch,
) -> DataProviderFacade:
    return DataProviderFacade(
        frames=(
            PairFrame(
                pair=base.pair,
                timeframe=base.timeframe,
                frame=strategy_frame_for_cursor(batch=base, visible_count=len(base.candles)),
            ),
            PairFrame(
                pair=informative_15m.pair,
                timeframe=informative_15m.timeframe,
                frame=strategy_frame_for_cursor(
                    batch=informative_15m,
                    visible_count=len(informative_15m.candles),
                ),
            ),
            PairFrame(
                pair=informative_1h.pair,
                timeframe=informative_1h.timeframe,
                frame=strategy_frame_for_cursor(
                    batch=informative_1h,
                    visible_count=len(informative_1h.candles),
                ),
            ),
        ),
    )


def _paper_ticks() -> tuple[PaperTick, ...]:
    started_at = datetime(2026, 1, 1, tzinfo=UTC)
    return tuple(
        PaperTick(
            pair=X7_PAIR,
            at=started_at + timedelta(minutes=index),
            price=Price(Decimal(100 + index)),
            signal_side=None,
        )
        for index in range(X7_PAPER_SAMPLE_TICKS)
    )


def _batch(
    *,
    pair: TradingPair,
    timeframe: str,
    candle_count: int,
    step: timedelta,
) -> CandleBatch:
    started_at = datetime(2026, 1, 1, tzinfo=UTC)
    candles = tuple(
        _candle(pair=pair, opened_at=started_at + (step * index), index=index)
        for index in range(candle_count)
    )
    return CandleBatch(pair=pair, timeframe=timeframe, candles=candles)


def _candle(*, pair: TradingPair, opened_at: datetime, index: int) -> Candle:
    close = Decimal(100) + Decimal(index % 17) + (Decimal(index) / Decimal(100))
    return Candle(
        pair=pair,
        opened_at=opened_at,
        open=Price(close - Decimal("0.40")),
        high=Price(close + Decimal("1.20")),
        low=Price(close - Decimal("1.10")),
        close=Price(close),
        volume=Quantity(ONE + Decimal(index % 5)),
    )


def _metadata() -> ReproducibilityMetadata:
    return ReproducibilityMetadata(
        config_hash="x7-benchmark-digest",
        strategy_hash="x7-native-strategy",
        data_hash=f"synthetic-{X7_BACKTEST_SAMPLE_CANDLES}-x7-candles",
        engine_version="0.1.0",
        git_commit=None,
        dependency_lock_hash="benchmark-lock",
        python_version="3.12.0",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        command_args=("benchmark", "m2", "x7-sample"),
    )
