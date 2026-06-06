from __future__ import annotations

from decimal import Decimal

from nfi_engine.backtest import BacktestRequest, run_backtest
from nfi_engine.data import CandleBatch
from nfi_engine.validation.models import (
    WalkForwardAggregateMetrics,
    WalkForwardRequest,
    WalkForwardResult,
    WalkForwardSplitResult,
    WalkForwardWindow,
)
from nfi_engine.validation.splits import generate_walk_forward_splits


def run_walk_forward(request: WalkForwardRequest) -> WalkForwardResult:
    windows = generate_walk_forward_splits(request.candles, split_count=request.split_count)
    splits = tuple(_run_window(request=request, window=window) for window in windows)
    return WalkForwardResult(
        splits=splits,
        aggregate_metrics=_aggregate_metrics(splits),
        metadata=request.metadata,
        profitability_claim=False,
    )


def _run_window(
    *,
    request: WalkForwardRequest,
    window: WalkForwardWindow,
) -> WalkForwardSplitResult:
    result = run_backtest(
        BacktestRequest(
            candles=_window_batch(candles=request.candles, window=window),
            adapter=request.adapter,
            settings=request.settings,
            config_digest=request.metadata.config_hash,
            strategy_name=request.strategy_name,
            metadata=request.metadata,
        ),
    )
    return WalkForwardSplitResult(
        role=window.role,
        start=window.start,
        end=window.end,
        candle_count=window.candle_count,
        total_trades=result.summary.total_trades,
        total_profit=result.summary.total_profit,
        final_balance=result.summary.final_balance,
    )


def _window_batch(*, candles: CandleBatch, window: WalkForwardWindow) -> CandleBatch:
    return CandleBatch(
        pair=candles.pair,
        timeframe=candles.timeframe,
        candles=candles.candles[window.start_index : window.end_index],
    )


def _aggregate_metrics(
    splits: tuple[WalkForwardSplitResult, ...],
) -> WalkForwardAggregateMetrics:
    if len(splits) == 0:
        return WalkForwardAggregateMetrics(
            total_trades=0,
            total_profit=Decimal(0),
            final_balance=Decimal(0),
        )
    return WalkForwardAggregateMetrics(
        total_trades=sum(split.total_trades for split in splits),
        total_profit=sum((split.total_profit for split in splits), Decimal(0)),
        final_balance=splits[-1].final_balance,
    )
