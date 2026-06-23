from __future__ import annotations

from nfi_engine.circuit_breakers import (
    CircuitBreakerDecision,
)
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.paper.breakers import (
    breaker_decision,
    first_breaker,
    protection_reasons,
    trading_halted,
)
from nfi_engine.paper.execution_models import (
    PaperExecutionContext,
    PaperExecutionResult,
    TickContext,
    TickExecution,
)
from nfi_engine.paper.models import BotState, PaperRunRequest, PaperTick
from nfi_engine.paper.order_execution import SignalTickContext, process_signal_tick
from nfi_engine.paper.signals import (
    first_entry_signal,
    signals_for_tick,
    strategy_rows_for_ticks,
    strategy_timeframe,
)
from nfi_engine.paper.timeline import TimelineContext, timeline_step
from nfi_engine.persistence import PersistenceDatabase
from nfi_engine.strategy import (
    StrategySignal,
)
from nfi_engine.strategy.timeline import (
    StrategyTimelineBuilder,
    TimelineSurface,
)

__all__ = [
    "execute_paper_events",
    "first_breaker",
    "trading_halted",
]


async def execute_paper_events(
    *,
    database: PersistenceDatabase,
    simulator: DeterministicExchangeSimulator,
    request: PaperRunRequest,
    state: BotState,
) -> PaperExecutionResult:
    processed_events = 0
    created_trades = 0
    blocked_orders = 0
    latest_decision: CircuitBreakerDecision | None = None
    previous_tick: PaperTick | None = None
    timeline = StrategyTimelineBuilder(surface=TimelineSurface.PAPER)
    context = PaperExecutionContext(
        database=database,
        simulator=simulator,
        request=request,
        state=state,
        strategy_rows=strategy_rows_for_ticks(request.ticks),
        strategy_timeframe=strategy_timeframe(request),
    )

    for sequence, tick in enumerate(request.ticks[: request.max_events], start=1):
        execution = await _execute_tick(
            context,
            TickContext(
                previous_tick=previous_tick,
                tick=tick,
                sequence=sequence,
                trade_number=created_trades + 1,
            ),
        )
        processed_events += 1
        created_trades += execution.created_trades
        blocked_orders += execution.blocked_orders
        latest_decision = execution.decision
        timeline.record(execution.timeline_step)
        previous_tick = tick

    return PaperExecutionResult(
        processed_events=processed_events,
        created_trades=created_trades,
        blocked_orders=blocked_orders,
        latest_decision=latest_decision,
        timeline=timeline.freeze(),
    )


async def _execute_tick(
    context: PaperExecutionContext,
    tick_context: TickContext,
) -> TickExecution:
    decision = breaker_decision(
        request=context.request,
        previous_tick=tick_context.previous_tick,
        current_tick=tick_context.tick,
    )
    signals = signals_for_tick(context=context, tick_context=tick_context)
    entry_signal = first_entry_signal(signals)
    blocked_by_protection = entry_signal is not None and decision.new_orders_blocked
    created_trades, blocked_orders = await _order_counts_for_tick(
        context=context,
        tick_context=tick_context,
        decision=decision,
        entry_signal=entry_signal,
    )
    return TickExecution(
        decision=decision,
        created_trades=created_trades,
        blocked_orders=blocked_orders,
        timeline_step=timeline_step(
            TimelineContext(
                request=context.request,
                tick=tick_context.tick,
                sequence=tick_context.sequence,
                created_this_tick=created_trades,
                created_trades_total=tick_context.trade_number - 1 + created_trades,
                signals=signals,
                blocked_by_protection=blocked_by_protection,
                protection_reasons=protection_reasons(decision),
            ),
        ),
    )


async def _order_counts_for_tick(
    *,
    context: PaperExecutionContext,
    tick_context: TickContext,
    decision: CircuitBreakerDecision,
    entry_signal: StrategySignal | None,
) -> tuple[int, int]:
    if context.state is not BotState.RUNNING or entry_signal is None:
        return 0, 0
    if decision.new_orders_blocked:
        return 0, 1
    created = await process_signal_tick(
        SignalTickContext(
            database=context.database,
            simulator=context.simulator,
            request=context.request,
            tick=tick_context.tick,
            side=entry_signal.side,
            trade_number=tick_context.trade_number,
            breaker_decision=decision,
        ),
    )
    return created, 0
