from __future__ import annotations

from typing import Protocol, runtime_checkable

from nfi_engine.domain import Leverage, PositionSide, StakeAmount, TradingPair
from nfi_engine.strategy.dtos import (
    StrategyMetadata,
    StrategyOrder,
    StrategySignal,
    StrategyTrade,
)
from nfi_engine.strategy.frame import StrategyFrame


class NativeStrategy(Protocol):
    def analyze(
        self,
        frame: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> tuple[StrategySignal, ...]: ...


@runtime_checkable
class RequiredFreqtradeStrategy(Protocol):
    timeframe: str
    can_short: bool

    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame: ...

    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame: ...

    def populate_exit_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame: ...


@runtime_checkable
class LeverageCallback(Protocol):
    def leverage(self, pair: TradingPair, current_leverage: Leverage) -> Leverage: ...


@runtime_checkable
class InformativePairsCallback(Protocol):
    def informative_pairs(self) -> tuple[tuple[str, str], ...]: ...


@runtime_checkable
class CustomExitCallback(Protocol):
    def custom_exit(self, trade: StrategyTrade) -> str | None: ...


@runtime_checkable
class CustomStakeAmountCallback(Protocol):
    def custom_stake_amount(
        self,
        pair: TradingPair,
        proposed_stake: StakeAmount,
    ) -> StakeAmount | None: ...


@runtime_checkable
class OrderFilledCallback(Protocol):
    def order_filled(self, order: StrategyOrder, trade: StrategyTrade) -> None: ...


@runtime_checkable
class AdjustTradePositionCallback(Protocol):
    def adjust_trade_position(self, trade: StrategyTrade) -> StakeAmount | None: ...


@runtime_checkable
class ConfirmTradeEntryCallback(Protocol):
    def confirm_trade_entry(self, pair: TradingPair, side: PositionSide) -> bool: ...


@runtime_checkable
class ConfirmTradeExitCallback(Protocol):
    def confirm_trade_exit(self, pair: TradingPair, side: PositionSide) -> bool: ...


@runtime_checkable
class BotLoopStartCallback(Protocol):
    def bot_loop_start(self) -> None: ...
