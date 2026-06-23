from __future__ import annotations

from typing import override

from nfi_engine.domain import Leverage, TradingPair
from nfi_engine.strategy import (
    SignalColumns,
    StrategyFrame,
    StrategyMetadata,
    StrategyOrder,
    StrategyTrade,
)


class NFISmokeStrategy:
    timeframe: str = "5m"
    can_short: bool = True

    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        return dataframe

    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        return dataframe.with_signal(
            index=-1,
            columns=SignalColumns(
                enter_long=True,
                enter_short=True,
                enter_tag="nfi-smoke",
            ),
        )

    def populate_exit_trend(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        return dataframe.with_signal(
            index=-1,
            columns=SignalColumns(exit_long=True, exit_short=True),
        )

    def informative_pairs(self) -> tuple[tuple[str, str], ...]:
        return (("BTC/USDT", "1h"),)

    def bot_loop_start(self) -> None:
        return None

    def leverage(self, _pair: TradingPair, _current_leverage: Leverage) -> Leverage:
        return Leverage.parse("3")

    def custom_exit(self, _trade: StrategyTrade) -> str | None:
        return None

    def order_filled(self, _order: StrategyOrder, _trade: StrategyTrade) -> None:
        return None


class LookaheadStrategy(NFISmokeStrategy):
    @override
    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        dataframe.future_rows()
        return dataframe


class MetadataLookupStrategy(NFISmokeStrategy):
    @override
    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        if metadata["pair"] != "ETH/USDT:USDT":
            return dataframe
        return dataframe.with_signal(
            index=-1,
            columns=SignalColumns(enter_long=True, enter_tag=metadata["timeframe"]),
        )

    @override
    def populate_exit_trend(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        return dataframe


class UnsupportedCallbackStrategy(NFISmokeStrategy):
    def custom_entry_price(self) -> str:
        return "unsupported"
