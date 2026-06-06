from __future__ import annotations

from nfi_engine.strategy import StrategyFrame, StrategyMetadata


class MissingEntryStrategy:
    timeframe: str = "5m"
    can_short: bool = False

    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        return dataframe

    def populate_exit_trend(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        return dataframe
