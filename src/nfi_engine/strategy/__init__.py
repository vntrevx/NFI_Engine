from __future__ import annotations

from nfi_engine.strategy.adapter import FreqtradeStrategyAdapter, load_freqtrade_strategy
from nfi_engine.strategy.callbacks import CALLBACK_NAMES
from nfi_engine.strategy.dtos import (
    CallbackSupportLevel,
    RunMode,
    StrategyCallbackSupport,
    StrategyInspection,
    StrategyMetadata,
    StrategyOrder,
    StrategySignal,
    StrategyTrade,
)
from nfi_engine.strategy.errors import StrategyContractError, StrategyErrorCode
from nfi_engine.strategy.frame import (
    SignalColumns,
    StrategyFeature,
    StrategyFeatureName,
    StrategyFrame,
    StrategyOhlcv,
    StrategyRow,
)
from nfi_engine.strategy.protocols import NativeStrategy, RequiredFreqtradeStrategy
from nfi_engine.strategy.provider import DataProviderFacade, PairFrame
from nfi_engine.strategy.timeline import (
    StrategyTimeline,
    StrategyTimelineBuilder,
    StrategyTimelineStep,
    TimelinePayload,
    TimelineStepPayload,
    TimelineSurface,
    count_strategy_signals,
    strategy_signal_sides,
    timeline_to_payload,
)

__all__ = [
    "CALLBACK_NAMES",
    "CallbackSupportLevel",
    "DataProviderFacade",
    "FreqtradeStrategyAdapter",
    "NativeStrategy",
    "PairFrame",
    "RequiredFreqtradeStrategy",
    "RunMode",
    "SignalColumns",
    "StrategyCallbackSupport",
    "StrategyContractError",
    "StrategyErrorCode",
    "StrategyFeature",
    "StrategyFeatureName",
    "StrategyFrame",
    "StrategyInspection",
    "StrategyMetadata",
    "StrategyOhlcv",
    "StrategyOrder",
    "StrategyRow",
    "StrategySignal",
    "StrategyTimeline",
    "StrategyTimelineBuilder",
    "StrategyTimelineStep",
    "StrategyTrade",
    "TimelinePayload",
    "TimelineStepPayload",
    "TimelineSurface",
    "count_strategy_signals",
    "load_freqtrade_strategy",
    "strategy_signal_sides",
    "timeline_to_payload",
]
