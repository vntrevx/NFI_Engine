from __future__ import annotations

import nfi_engine.backtest.frames as frames  # noqa: PLR0402
from nfi_engine.backtest.closing import (
    close_open_trades_at_end,
    close_signal_trades,
    close_stopped_trades,
)
from nfi_engine.backtest.execution import EntryContext, open_signal_trades
from nfi_engine.backtest.models import (
    BacktestRequest,
    BacktestResult,
    EquityPoint,
    OpenTrade,
    StrategySummary,
    TradeRecord,
)
from nfi_engine.backtest.summary import summarize_backtest
from nfi_engine.backtest.validation import validate_request
from nfi_engine.domain import SignalType
from nfi_engine.strategy import RunMode, StrategyMetadata
from nfi_engine.strategy.timeline import (
    StrategyTimelineBuilder,
    StrategyTimelineStep,
    TimelineSurface,
    count_strategy_signals,
    strategy_signal_reasons,
    strategy_signal_sides,
)


def run_backtest(request: BacktestRequest) -> BacktestResult:
    validate_request(request)
    inspection = request.adapter.inspect()
    metadata = StrategyMetadata(
        pair=request.candles.pair,
        timeframe=request.candles.timeframe,
        runmode=RunMode.BACKTEST,
    )
    open_trades: tuple[OpenTrade, ...] = ()
    closed_trades: list[TradeRecord] = []
    equity_curve: list[EquityPoint] = []
    rejected_entries = 0
    realized_equity = request.settings.starting_balance
    timeline = StrategyTimelineBuilder(surface=TimelineSurface.BACKTEST)
    strategy_rows = frames.strategy_rows_for_batch(batch=request.candles)
    for index, candle in enumerate(request.candles.candles, start=1):
        stop_result = close_stopped_trades(
            open_trades=open_trades,
            candle=candle,
            settings=request.settings,
        )
        open_trades = stop_result.open_trades
        closed_trades.extend(stop_result.closed_trades)
        realized_equity += stop_result.profit
        frame = frames.strategy_frame_from_rows(rows=strategy_rows, visible_count=index)
        signals = request.adapter.analyze(frame, metadata, incremental=True)
        exit_result = close_signal_trades(
            open_trades=open_trades,
            candle=candle,
            settings=request.settings,
            signals=signals,
        )
        open_trades = exit_result.open_trades
        closed_trades.extend(exit_result.closed_trades)
        realized_equity += exit_result.profit
        open_count_before_entry = len(open_trades)
        entry_signal_count = count_strategy_signals(signals, SignalType.ENTER)
        entry_result = open_signal_trades(
            open_trades=open_trades,
            signals=signals,
            context=EntryContext(
                candle=candle,
                settings=request.settings,
                next_trade_number=1 + len(closed_trades) + len(open_trades),
                can_short=inspection.can_short,
            ),
        )
        open_trades = entry_result.open_trades
        rejected_entries += entry_result.rejected_entries
        timeline.record(
            StrategyTimelineStep(
                sequence=index,
                pair=request.candles.pair,
                at=candle.opened_at,
                indicator_runs=1,
                entry_signals=entry_signal_count,
                exit_signals=count_strategy_signals(signals, SignalType.EXIT),
                entry_sides=strategy_signal_sides(signals, SignalType.ENTER),
                exit_sides=strategy_signal_sides(signals, SignalType.EXIT),
                opened_orders=len(open_trades) - open_count_before_entry,
                closed_orders=len(stop_result.closed_trades) + len(exit_result.closed_trades),
                rejected_actions=entry_result.rejected_entries + exit_result.rejected_signals,
                blocked_actions=0,
                protection_active=len(stop_result.closed_trades) > 0,
                stake_amount=request.settings.stake_amount if entry_signal_count > 0 else None,
                leverage=request.settings.leverage if entry_signal_count > 0 else None,
                open_trade_count=len(open_trades),
                entry_reasons=strategy_signal_reasons(
                    signals,
                    SignalType.ENTER,
                    fallback="signal",
                ),
                exit_reasons=strategy_signal_reasons(
                    signals,
                    SignalType.EXIT,
                    fallback="signal",
                ),
            ),
        )
        equity_curve.append(EquityPoint(opened_at=candle.opened_at, equity=realized_equity))
    final_result = close_open_trades_at_end(
        open_trades=open_trades,
        candle=request.candles.candles[-1],
        settings=request.settings,
    )
    closed_trades.extend(final_result.closed_trades)
    realized_equity += final_result.profit
    trade_records = tuple(closed_trades)
    equity_points = tuple(equity_curve)
    return BacktestResult(
        trades=trade_records,
        equity_curve=equity_points,
        summary=summarize_backtest(
            settings=request.settings,
            final_balance=realized_equity,
            trades=trade_records,
            equity_curve=equity_points,
            rejected_entries=rejected_entries,
        ),
        config_digest=request.config_digest,
        strategy=StrategySummary(
            name=request.strategy_name,
            timeframe=inspection.timeframe,
            can_short=inspection.can_short,
        ),
        metadata=request.metadata,
        timeline=timeline.freeze(),
    )
