from __future__ import annotations

from typing import Final, override

from nfi_engine.strategy import SignalColumns, StrategyFrame, StrategyMetadata

FIRST_OPEN: Final = "2026-01-01T00:00:00+00:00"
SECOND_OPEN: Final = "2026-01-01T00:05:00+00:00"
THIRD_OPEN: Final = "2026-01-01T00:10:00+00:00"


class NoSignalStrategy:
    timeframe: str = "5m"
    can_short: bool = False

    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        if metadata.timeframe != self.timeframe:
            return dataframe
        return dataframe

    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        if metadata.timeframe != self.timeframe:
            return dataframe
        return dataframe

    def populate_exit_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        if metadata.timeframe != self.timeframe:
            return dataframe
        return dataframe


class LongExitStrategy(NoSignalStrategy):
    @override
    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        if dataframe.last_visible_row().date == FIRST_OPEN:
            return dataframe.with_signal(
                index=-1,
                columns=SignalColumns(enter_long=True, enter_tag="unit-long"),
            )
        return dataframe

    @override
    def populate_exit_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        dataframe = super().populate_exit_trend(dataframe, metadata)
        if dataframe.last_visible_row().date == THIRD_OPEN:
            return dataframe.with_signal(index=-1, columns=SignalColumns(exit_long=True))
        return dataframe


class ShortExitStrategy(NoSignalStrategy):
    can_short: bool = True

    @override
    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        if dataframe.last_visible_row().date == FIRST_OPEN:
            return dataframe.with_signal(
                index=-1,
                columns=SignalColumns(enter_short=True, enter_tag="unit-short"),
            )
        return dataframe

    @override
    def populate_exit_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        dataframe = super().populate_exit_trend(dataframe, metadata)
        if dataframe.last_visible_row().date == THIRD_OPEN:
            return dataframe.with_signal(index=-1, columns=SignalColumns(exit_short=True))
        return dataframe


class StoplossLongStrategy(NoSignalStrategy):
    @override
    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        if dataframe.last_visible_row().date == FIRST_OPEN:
            return dataframe.with_signal(
                index=-1,
                columns=SignalColumns(enter_long=True, enter_tag="unit-stop"),
            )
        return dataframe


class EveryCandleLongStrategy(NoSignalStrategy):
    @override
    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        dataframe = super().populate_entry_trend(dataframe, metadata)
        return dataframe.with_signal(
            index=-1,
            columns=SignalColumns(enter_long=True, enter_tag="unit-max-open"),
        )
