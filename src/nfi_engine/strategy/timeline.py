from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique
from typing import Final, TypedDict

from nfi_engine.domain import PositionSide, SignalType, TradingPair
from nfi_engine.strategy.dtos import StrategySignal

DEFAULT_TIMELINE_MAX_STEPS: Final = 512


@unique
class TimelineSurface(StrEnum):
    BACKTEST = "backtest"
    PAPER = "paper"


@dataclass(frozen=True, slots=True)
class StrategyTimelineStep:
    sequence: int
    pair: TradingPair
    at: datetime
    indicator_runs: int
    entry_signals: int
    exit_signals: int
    entry_sides: tuple[PositionSide, ...]
    exit_sides: tuple[PositionSide, ...]
    opened_orders: int
    closed_orders: int
    rejected_actions: int
    blocked_actions: int
    protection_active: bool
    stake_amount: Decimal | None
    leverage: Decimal | None
    open_trade_count: int
    entry_reasons: tuple[str, ...] = ()
    protection_reasons: tuple[str, ...] = ()
    exit_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class StrategyTimeline:
    surface: TimelineSurface
    max_steps: int
    truncated: bool
    steps: tuple[StrategyTimelineStep, ...]


@dataclass(slots=True)
class StrategyTimelineBuilder:
    """Mutable accumulator used to avoid rebuilding tuple state per candle."""

    surface: TimelineSurface
    max_steps: int = DEFAULT_TIMELINE_MAX_STEPS
    _steps: list[StrategyTimelineStep] = field(default_factory=list, init=False)
    _truncated: bool = field(default=False, init=False)

    def record(self, step: StrategyTimelineStep) -> None:
        if len(self._steps) >= self.max_steps:
            self._truncated = True
            return
        self._steps.append(step)

    def freeze(self) -> StrategyTimeline:
        return StrategyTimeline(
            surface=self.surface,
            max_steps=self.max_steps,
            truncated=self._truncated,
            steps=tuple(self._steps),
        )


class TimelineStepPayload(TypedDict):
    sequence: int
    pair: str
    at: str
    indicator_runs: int
    entry_signals: int
    exit_signals: int
    entry_sides: list[str]
    exit_sides: list[str]
    opened_orders: int
    closed_orders: int
    rejected_actions: int
    blocked_actions: int
    protection_active: bool
    entry_reasons: list[str]
    protection_reasons: list[str]
    stake_amount: str | None
    leverage: str | None
    open_trade_count: int
    exit_reasons: list[str]


class TimelinePayload(TypedDict):
    surface: str
    step_count: int
    max_steps: int
    truncated: bool
    payload_bytes: int
    steps: list[TimelineStepPayload]


def count_strategy_signals(
    signals: tuple[StrategySignal, ...],
    signal_type: SignalType,
) -> int:
    return sum(1 for signal in signals if signal.signal_type is signal_type)


def strategy_signal_sides(
    signals: tuple[StrategySignal, ...],
    signal_type: SignalType,
) -> tuple[PositionSide, ...]:
    return tuple(signal.side for signal in signals if signal.signal_type is signal_type)


def strategy_signal_reasons(
    signals: tuple[StrategySignal, ...],
    signal_type: SignalType,
    fallback: str,
) -> tuple[str, ...]:
    return tuple(
        signal.tag if signal.tag is not None else fallback
        for signal in signals
        if signal.signal_type is signal_type
    )


def timeline_to_payload(timeline: StrategyTimeline) -> TimelinePayload:
    steps = [_step_to_payload(step) for step in timeline.steps]
    return TimelinePayload(
        surface=timeline.surface.value,
        step_count=len(steps),
        max_steps=timeline.max_steps,
        truncated=timeline.truncated,
        payload_bytes=_payload_bytes(steps),
        steps=steps,
    )


def _step_to_payload(step: StrategyTimelineStep) -> TimelineStepPayload:
    return TimelineStepPayload(
        sequence=step.sequence,
        pair=str(step.pair.normalized),
        at=step.at.isoformat(),
        indicator_runs=step.indicator_runs,
        entry_signals=step.entry_signals,
        exit_signals=step.exit_signals,
        entry_sides=[side.value for side in step.entry_sides],
        exit_sides=[side.value for side in step.exit_sides],
        opened_orders=step.opened_orders,
        closed_orders=step.closed_orders,
        rejected_actions=step.rejected_actions,
        blocked_actions=step.blocked_actions,
        protection_active=step.protection_active,
        entry_reasons=list(step.entry_reasons),
        protection_reasons=list(step.protection_reasons),
        stake_amount=_decimal_payload(step.stake_amount),
        leverage=_decimal_payload(step.leverage),
        open_trade_count=step.open_trade_count,
        exit_reasons=list(step.exit_reasons),
    )


def _decimal_payload(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return str(value)


def _payload_bytes(steps: list[TimelineStepPayload]) -> int:
    return len(
        json.dumps(
            steps,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    )
