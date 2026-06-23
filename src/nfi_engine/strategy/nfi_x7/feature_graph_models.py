from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Final

from nfi_engine.domain import TradingPair
from nfi_engine.strategy.frame import StrategyFeatureName, StrategyFrame
from nfi_engine.strategy.provider import DataProviderFacade

X7_FEATURE_GRAPH_CACHE_LIMIT: Final = 4
X7_FEATURE_GRAPH_FEATURE_BUDGET: Final = 64


@dataclass(frozen=True, slots=True)
class X7FeatureGraphRequest:
    pair: TradingPair
    base_timeframe: str
    informative_timeframes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class X7FeatureGraphContext:
    base_frame: StrategyFrame
    provider: DataProviderFacade
    request: X7FeatureGraphRequest


@dataclass(frozen=True, slots=True)
class X7FeatureGraphCoverage:
    base_feature_count: int
    informative_feature_count: int
    informative_timeframes: tuple[str, ...]
    feature_names: tuple[StrategyFeatureName, ...]

    @property
    def total_feature_count(self) -> int:
        return self.base_feature_count + self.informative_feature_count


@dataclass(frozen=True, slots=True)
class X7FeatureGraphResult:
    frame: StrategyFrame
    coverage: X7FeatureGraphCoverage
    cache_hit: bool = field(default=False, compare=False)


@dataclass(frozen=True, slots=True)
class X7FeatureGraphCacheStats:
    hit_count: int
    miss_count: int
    entry_count: int


@dataclass(frozen=True, slots=True)
class X7FrameCursorSignature:
    row_count: int
    first_date: str | None
    last_date: str | None
    close_sum: Decimal
    high_sum: Decimal
    low_sum: Decimal
    volume_sum: Decimal


@dataclass(frozen=True, slots=True)
class X7InformativeCursorSignature:
    source: str
    timeframe: str
    frame: X7FrameCursorSignature


@dataclass(frozen=True, slots=True)
class X7FeatureGraphCacheKey:
    pair: TradingPair
    base_timeframe: str
    base_frame: X7FrameCursorSignature
    informative_frames: tuple[X7InformativeCursorSignature, ...]
