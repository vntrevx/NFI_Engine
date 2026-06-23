from __future__ import annotations

from dataclasses import dataclass

from nfi_engine.domain import SignalType
from nfi_engine.paper.models import PaperRunRequest, PaperTick
from nfi_engine.strategy import StrategySignal
from nfi_engine.strategy.timeline import (
    StrategyTimelineStep,
    count_strategy_signals,
    strategy_signal_reasons,
    strategy_signal_sides,
)


@dataclass(frozen=True, slots=True)
class TimelineContext:
    request: PaperRunRequest
    tick: PaperTick
    sequence: int
    created_this_tick: int
    created_trades_total: int
    signals: tuple[StrategySignal, ...]
    blocked_by_protection: bool
    protection_reasons: tuple[str, ...]


def timeline_step(context: TimelineContext) -> StrategyTimelineStep:
    entry_signal_count = count_strategy_signals(context.signals, SignalType.ENTER)
    signal_rejected = (
        entry_signal_count > 0
        and not context.blocked_by_protection
        and context.created_this_tick == 0
    )
    return StrategyTimelineStep(
        sequence=context.sequence,
        pair=context.tick.pair,
        at=context.tick.at,
        indicator_runs=1 if context.request.strategy_adapter is not None else 0,
        entry_signals=entry_signal_count,
        exit_signals=0,
        entry_sides=strategy_signal_sides(context.signals, SignalType.ENTER),
        exit_sides=(),
        opened_orders=context.created_this_tick,
        closed_orders=0,
        rejected_actions=1 if signal_rejected else 0,
        blocked_actions=1 if context.blocked_by_protection else 0,
        protection_active=context.blocked_by_protection,
        protection_reasons=(context.protection_reasons if context.blocked_by_protection else ()),
        stake_amount=(context.request.settings.risk.stake_usdt if entry_signal_count > 0 else None),
        leverage=context.request.settings.risk.leverage if entry_signal_count > 0 else None,
        open_trade_count=context.created_trades_total,
        entry_reasons=strategy_signal_reasons(
            context.signals,
            SignalType.ENTER,
            fallback="signal",
        ),
    )
