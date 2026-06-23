from __future__ import annotations

from decimal import Decimal

from nfi_engine.domain import SignalType
from nfi_engine.paper.execution_models import PaperExecutionContext, TickContext
from nfi_engine.paper.models import PaperRunRequest, PaperTick
from nfi_engine.strategy import (
    RunMode,
    StrategyMetadata,
    StrategyOhlcv,
    StrategyRow,
    StrategySignal,
)
from nfi_engine.strategy.frame import StrategyFrame


def signals_for_tick(
    *,
    context: PaperExecutionContext,
    tick_context: TickContext,
) -> tuple[StrategySignal, ...]:
    adapter = context.request.strategy_adapter
    if adapter is None:
        side = tick_context.tick.signal_side
        if side is None:
            return ()
        return (
            StrategySignal(
                pair=tick_context.tick.pair,
                side=side,
                signal_type=SignalType.ENTER,
            ),
        )
    timeframe = context.strategy_timeframe
    if timeframe is None:
        return ()
    return adapter.analyze(
        StrategyFrame(
            rows=context.strategy_rows,
            visible_row_count=tick_context.sequence,
        ),
        StrategyMetadata(
            pair=tick_context.tick.pair,
            timeframe=timeframe,
            runmode=RunMode.DRY_RUN,
        ),
        incremental=True,
    )


def first_entry_signal(signals: tuple[StrategySignal, ...]) -> StrategySignal | None:
    for signal in signals:
        if signal.signal_type is SignalType.ENTER:
            return signal
    return None


def strategy_rows_for_ticks(ticks: tuple[PaperTick, ...]) -> tuple[StrategyRow, ...]:
    return tuple(
        StrategyRow(
            date=tick.at.isoformat(),
            close=tick.price,
            ohlcv=StrategyOhlcv(
                open=tick.price,
                high=tick.price,
                low=tick.price,
                close=tick.price,
                volume=Decimal(1),
            ),
        )
        for tick in ticks
    )


def strategy_timeframe(request: PaperRunRequest) -> str | None:
    adapter = request.strategy_adapter
    if adapter is None:
        return None
    return adapter.inspect().timeframe
