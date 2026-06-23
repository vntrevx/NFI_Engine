from __future__ import annotations

from dataclasses import dataclass

from nfi_engine.circuit_breakers import CircuitBreakerDecision
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.paper.models import BotState, PaperRunRequest, PaperTick
from nfi_engine.persistence import PersistenceDatabase
from nfi_engine.strategy import StrategyRow
from nfi_engine.strategy.timeline import StrategyTimeline, StrategyTimelineStep


@dataclass(frozen=True, slots=True)
class PaperExecutionResult:
    processed_events: int
    created_trades: int
    blocked_orders: int
    latest_decision: CircuitBreakerDecision | None
    timeline: StrategyTimeline


@dataclass(frozen=True, slots=True)
class PaperExecutionContext:
    database: PersistenceDatabase
    simulator: DeterministicExchangeSimulator
    request: PaperRunRequest
    state: BotState
    strategy_rows: tuple[StrategyRow, ...]
    strategy_timeframe: str | None


@dataclass(frozen=True, slots=True)
class TickExecution:
    decision: CircuitBreakerDecision
    created_trades: int
    blocked_orders: int
    timeline_step: StrategyTimelineStep


@dataclass(frozen=True, slots=True)
class TickContext:
    previous_tick: PaperTick | None
    tick: PaperTick
    sequence: int
    trade_number: int
