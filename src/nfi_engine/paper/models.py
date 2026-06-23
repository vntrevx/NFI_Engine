from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, unique

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import AccountSnapshot, PositionSide, Price, TradingPair
from nfi_engine.strategy import FreqtradeStrategyAdapter
from nfi_engine.strategy.timeline import StrategyTimeline


@unique
class BotState(StrEnum):
    STOPPED = "stopped"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"


@unique
class BotCommand(StrEnum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"


@dataclass(frozen=True, slots=True)
class PaperTick:
    pair: TradingPair
    at: datetime
    price: Price
    signal_side: PositionSide | None


@dataclass(frozen=True, slots=True)
class PaperRunRequest:
    settings: RuntimeSettings
    ticks: tuple[PaperTick, ...]
    max_events: int
    database_url: str
    strategy_adapter: FreqtradeStrategyAdapter | None = None
    account_snapshot: AccountSnapshot | None = None


@dataclass(frozen=True, slots=True)
class PaperRunResult:
    processed_events: int
    created_trades: int
    live_orders: bool
    final_state: BotState
    trading_halted: bool
    halted_breaker: str | None
    new_orders_blocked: bool
    timeline: StrategyTimeline
