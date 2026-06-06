from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique

from nfi_engine.backtest import ReproducibilityMetadata, SimulationSettings
from nfi_engine.data import CandleBatch
from nfi_engine.strategy import FreqtradeStrategyAdapter


@unique
class WalkForwardRole(StrEnum):
    TRAIN = "train"
    VALIDATION = "validation"
    TEST = "test"


@dataclass(frozen=True, slots=True)
class WalkForwardWindow:
    role: WalkForwardRole
    start_index: int
    end_index: int
    start: datetime
    end: datetime
    candle_count: int


@dataclass(frozen=True, slots=True)
class WalkForwardRequest:
    candles: CandleBatch
    adapter: FreqtradeStrategyAdapter
    settings: SimulationSettings
    strategy_name: str
    metadata: ReproducibilityMetadata
    split_count: int


@dataclass(frozen=True, slots=True)
class WalkForwardSplitResult:
    role: WalkForwardRole
    start: datetime
    end: datetime
    candle_count: int
    total_trades: int
    total_profit: Decimal
    final_balance: Decimal


@dataclass(frozen=True, slots=True)
class WalkForwardAggregateMetrics:
    total_trades: int
    total_profit: Decimal
    final_balance: Decimal


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    splits: tuple[WalkForwardSplitResult, ...]
    aggregate_metrics: WalkForwardAggregateMetrics
    metadata: ReproducibilityMetadata
    profitability_claim: bool
