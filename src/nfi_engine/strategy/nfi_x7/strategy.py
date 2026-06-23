from __future__ import annotations

from typing import Final

from nfi_engine.domain import Leverage, PositionSide, StakeAmount, TradingPair
from nfi_engine.strategy import DataProviderFacade
from nfi_engine.strategy.dtos import StrategyMetadata, StrategyOrder, StrategyTrade
from nfi_engine.strategy.frame import StrategyFrame
from nfi_engine.strategy.nfi_x7.entries import apply_x7_entry_decision
from nfi_engine.strategy.nfi_x7.exits import (
    apply_x7_exit_decision,
    build_x7_custom_exit_decision,
)
from nfi_engine.strategy.nfi_x7.feature_graph import X7FeatureGraph
from nfi_engine.strategy.nfi_x7.feature_graph_models import (
    X7FeatureGraphContext,
    X7FeatureGraphRequest,
)
from nfi_engine.strategy.nfi_x7.metadata import X7_METADATA
from nfi_engine.strategy.nfi_x7.positioning import (
    X7_DEFAULT_LEVERAGE as POSITIONING_DEFAULT_LEVERAGE,
)
from nfi_engine.strategy.nfi_x7.positioning import (
    X7LeverageContext,
    X7PositionAdjustmentContext,
    X7StakeContext,
    build_x7_leverage_decision,
    build_x7_order_filled_snapshot,
    build_x7_position_adjustment_decision,
    build_x7_stake_decision,
)
from nfi_engine.strategy.nfi_x7.protections import (
    X7LoopHookContext,
    X7TradeConfirmationContext,
    build_x7_loop_hook_decision,
    build_x7_trade_confirmation_decision,
)
from nfi_engine.strategy.nfi_x7.requirements import X7_DATA_REQUIREMENTS

X7_DEFAULT_LEVERAGE: Final = POSITIONING_DEFAULT_LEVERAGE
X7_DEFAULT_BTC_REFERENCE_PAIR: Final = "BTC/USDT:USDT"
X7_BASE_ONLY_PROVIDER: Final = DataProviderFacade(frames=())


class X7NativeStrategy:
    """Keeps a small native feature graph cache across strategy callbacks."""

    timeframe: str = X7_METADATA.base_timeframe
    can_short: bool = True

    def __init__(self) -> None:
        self._feature_graph: X7FeatureGraph = X7FeatureGraph()

    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        return self._feature_graph.build(
            X7FeatureGraphContext(
                base_frame=dataframe,
                provider=X7_BASE_ONLY_PROVIDER,
                request=X7FeatureGraphRequest(
                    pair=metadata.pair,
                    base_timeframe=metadata.timeframe,
                    informative_timeframes=(),
                ),
            ),
        ).frame

    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        return apply_x7_entry_decision(dataframe)

    def populate_exit_trend(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        return apply_x7_exit_decision(dataframe)

    def informative_pairs(self) -> tuple[tuple[str, str], ...]:
        return tuple(
            (X7_DEFAULT_BTC_REFERENCE_PAIR, timeframe)
            for timeframe in X7_DATA_REQUIREMENTS.informative_timeframes
        )

    def custom_exit(self, trade: StrategyTrade) -> str | None:
        return build_x7_custom_exit_decision(trade).exit_reason

    def custom_stake_amount(
        self,
        _pair: TradingPair,
        proposed_stake: StakeAmount,
    ) -> StakeAmount:
        return build_x7_stake_decision(
            X7StakeContext(proposed_stake=proposed_stake),
        ).stake

    def order_filled(self, order: StrategyOrder, trade: StrategyTrade) -> None:
        build_x7_order_filled_snapshot(order=order, trade=trade)

    def adjust_trade_position(self, trade: StrategyTrade) -> StakeAmount | None:
        return build_x7_position_adjustment_decision(
            X7PositionAdjustmentContext(trade=trade),
        ).stake

    def confirm_trade_entry(self, pair: TradingPair, side: PositionSide) -> bool:
        return build_x7_trade_confirmation_decision(
            X7TradeConfirmationContext(pair=pair, side=side),
        ).allowed

    def confirm_trade_exit(self, pair: TradingPair, side: PositionSide) -> bool:
        return build_x7_trade_confirmation_decision(
            X7TradeConfirmationContext(pair=pair, side=side),
        ).allowed

    def bot_loop_start(self) -> None:
        _ = build_x7_loop_hook_decision(X7LoopHookContext())

    def leverage(self, _pair: TradingPair, _current_leverage: Leverage) -> Leverage:
        return build_x7_leverage_decision(X7LeverageContext()).leverage
