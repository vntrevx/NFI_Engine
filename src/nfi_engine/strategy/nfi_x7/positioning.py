from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum, unique
from typing import Final

from nfi_engine.domain import (
    Leverage,
    OrderId,
    PositionSide,
    StakeAmount,
    TradeId,
    TradingPair,
)
from nfi_engine.strategy.dtos import StrategyOrder, StrategyTrade

X7_DEFAULT_LEVERAGE: Final = Leverage.parse("3")
ZERO: Final = Decimal(0)


@unique
class X7StakeReason(StrEnum):
    ACCEPTED = "STAKE_ACCEPTED"
    CAPPED_BY_ALLOCATION = "STAKE_CAPPED_BY_ALLOCATION"
    CAPPED_BY_AVAILABLE = "STAKE_CAPPED_BY_AVAILABLE"


@unique
class X7LeverageReason(StrEnum):
    DEFAULT = "LEVERAGE_DEFAULT_3X"
    CAPPED = "LEVERAGE_CAPPED"


@unique
class X7PositionAdjustmentReason(StrEnum):
    NO_ADJUSTMENT = "POSITION_ADJUSTMENT_NONE"
    ACCEPTED = "POSITION_ADJUSTMENT_ACCEPTED"
    CAPPED_BY_MAX = "POSITION_ADJUSTMENT_CAPPED_BY_MAX"
    CAPPED_BY_AVAILABLE = "POSITION_ADJUSTMENT_CAPPED_BY_AVAILABLE"


@dataclass(frozen=True, slots=True)
class X7StakeContext:
    proposed_stake: StakeAmount
    available_balance: StakeAmount | None = None
    allocation_cap: StakeAmount | None = None


@dataclass(frozen=True, slots=True)
class X7StakeDecision:
    stake: StakeAmount
    reason: X7StakeReason
    capped: bool


@dataclass(frozen=True, slots=True)
class X7LeverageContext:
    requested_leverage: Leverage = X7_DEFAULT_LEVERAGE
    max_leverage: Leverage | None = None


@dataclass(frozen=True, slots=True)
class X7LeverageDecision:
    leverage: Leverage
    reason: X7LeverageReason
    capped: bool


@dataclass(frozen=True, slots=True)
class X7OrderFilledSnapshot:
    order_id: OrderId
    trade_id: TradeId
    pair: TradingPair
    side: PositionSide
    pair_and_side_match: bool


@dataclass(frozen=True, slots=True)
class X7PositionAdjustmentContext:
    trade: StrategyTrade
    proposed_stake: StakeAmount | None = None
    max_adjustment: StakeAmount | None = None
    available_balance: StakeAmount | None = None


@dataclass(frozen=True, slots=True)
class X7PositionAdjustmentDecision:
    stake: StakeAmount | None
    reason: X7PositionAdjustmentReason
    capped: bool


def build_x7_stake_decision(context: X7StakeContext) -> X7StakeDecision:
    stake = context.proposed_stake
    reason = X7StakeReason.ACCEPTED
    if context.allocation_cap is not None and stake > context.allocation_cap:
        stake = context.allocation_cap
        reason = X7StakeReason.CAPPED_BY_ALLOCATION
    if context.available_balance is not None and stake > context.available_balance:
        stake = context.available_balance
        reason = X7StakeReason.CAPPED_BY_AVAILABLE
    return X7StakeDecision(
        stake=stake,
        reason=reason,
        capped=reason is not X7StakeReason.ACCEPTED,
    )


def build_x7_leverage_decision(context: X7LeverageContext) -> X7LeverageDecision:
    max_leverage = context.max_leverage
    if max_leverage is not None:
        exceeds_max = context.requested_leverage.value > max_leverage.value
        if exceeds_max:
            return X7LeverageDecision(
                leverage=max_leverage,
                reason=X7LeverageReason.CAPPED,
                capped=True,
            )
    return X7LeverageDecision(
        leverage=context.requested_leverage,
        reason=X7LeverageReason.DEFAULT,
        capped=False,
    )


def build_x7_order_filled_snapshot(
    *,
    order: StrategyOrder,
    trade: StrategyTrade,
) -> X7OrderFilledSnapshot:
    return X7OrderFilledSnapshot(
        order_id=order.order_id,
        trade_id=trade.trade_id,
        pair=trade.pair,
        side=trade.side,
        pair_and_side_match=order.pair == trade.pair and order.side is trade.side,
    )


def build_x7_position_adjustment_decision(
    context: X7PositionAdjustmentContext,
) -> X7PositionAdjustmentDecision:
    if context.proposed_stake is None or context.proposed_stake <= ZERO:
        return X7PositionAdjustmentDecision(
            stake=None,
            reason=X7PositionAdjustmentReason.NO_ADJUSTMENT,
            capped=False,
        )
    stake = context.proposed_stake
    reason = X7PositionAdjustmentReason.ACCEPTED
    if context.max_adjustment is not None and stake > context.max_adjustment:
        stake = context.max_adjustment
        reason = X7PositionAdjustmentReason.CAPPED_BY_MAX
    if context.available_balance is not None and stake > context.available_balance:
        stake = context.available_balance
        reason = X7PositionAdjustmentReason.CAPPED_BY_AVAILABLE
    return X7PositionAdjustmentDecision(
        stake=stake,
        reason=reason,
        capped=reason is not X7PositionAdjustmentReason.ACCEPTED,
    )
