from __future__ import annotations

from nfi_engine.backtest.closing import (
    close_open_trades_at_end,
    close_signal_trades,
    close_stopped_trades,
)
from nfi_engine.backtest.execution import EntryContext, open_signal_trades
from nfi_engine.backtest.frames import strategy_frame_for_cursor
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
from nfi_engine.strategy import RunMode, StrategyMetadata


def run_backtest(request: BacktestRequest) -> BacktestResult:
    validate_request(request)
    inspection = request.adapter.inspect()
    metadata = StrategyMetadata(
        pair=request.candles.pair,
        timeframe=request.candles.timeframe,
        runmode=RunMode.BACKTEST,
    )
    open_trades: tuple[OpenTrade, ...] = ()
    closed_trades: tuple[TradeRecord, ...] = ()
    equity_curve: tuple[EquityPoint, ...] = ()
    rejected_entries = 0
    realized_equity = request.settings.starting_balance
    for index, candle in enumerate(request.candles.candles, start=1):
        stop_result = close_stopped_trades(
            open_trades=open_trades,
            candle=candle,
            settings=request.settings,
        )
        open_trades = stop_result.open_trades
        closed_trades += stop_result.closed_trades
        realized_equity += stop_result.profit
        frame = strategy_frame_for_cursor(batch=request.candles, visible_count=index)
        signals = request.adapter.analyze(frame, metadata, incremental=True)
        exit_result = close_signal_trades(
            open_trades=open_trades,
            candle=candle,
            settings=request.settings,
            signals=signals,
        )
        open_trades = exit_result.open_trades
        closed_trades += exit_result.closed_trades
        realized_equity += exit_result.profit
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
        equity_curve += (EquityPoint(opened_at=candle.opened_at, equity=realized_equity),)
    final_result = close_open_trades_at_end(
        open_trades=open_trades,
        candle=request.candles.candles[-1],
        settings=request.settings,
    )
    closed_trades += final_result.closed_trades
    realized_equity += final_result.profit
    return BacktestResult(
        trades=closed_trades,
        equity_curve=equity_curve,
        summary=summarize_backtest(
            settings=request.settings,
            final_balance=realized_equity,
            trades=closed_trades,
            equity_curve=equity_curve,
            rejected_entries=rejected_entries,
        ),
        config_digest=request.config_digest,
        strategy=StrategySummary(
            name=request.strategy_name,
            timeframe=inspection.timeframe,
            can_short=inspection.can_short,
        ),
        metadata=request.metadata,
    )
