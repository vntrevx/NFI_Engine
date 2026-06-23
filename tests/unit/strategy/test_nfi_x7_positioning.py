from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Final

from nfi_engine.domain import (
    AccountSnapshot,
    Leverage,
    OrderId,
    PositionSide,
    StakeAmount,
    TradeId,
    TradingMode,
    TradingPair,
)
from nfi_engine.risk import (
    AcceptedOrderQuote,
    RiskPolicy,
    RiskRequest,
    quote_order,
)
from nfi_engine.strategy import StrategyOrder, StrategyTrade
from nfi_engine.strategy.nfi_x7.positioning import (
    X7LeverageContext,
    X7LeverageReason,
    X7PositionAdjustmentContext,
    X7PositionAdjustmentReason,
    X7StakeContext,
    X7StakeReason,
    build_x7_leverage_decision,
    build_x7_order_filled_snapshot,
    build_x7_position_adjustment_decision,
    build_x7_stake_decision,
)

NOW: Final = datetime(2026, 6, 20, tzinfo=UTC)


def test_x7_stake_decision_caps_to_wallet_and_allocation_limits() -> None:
    # Given
    context = X7StakeContext(
        proposed_stake=StakeAmount(Decimal(100)),
        available_balance=StakeAmount(Decimal(80)),
        allocation_cap=StakeAmount(Decimal(60)),
    )

    # When
    decision = build_x7_stake_decision(context)

    # Then
    assert decision.stake == StakeAmount(Decimal(60))
    assert decision.reason is X7StakeReason.CAPPED_BY_ALLOCATION
    assert decision.capped is True


def test_x7_default_leverage_is_three_and_risk_service_caps_above_policy_max() -> None:
    # Given
    pair = TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
    leverage_decision = build_x7_leverage_decision(
        X7LeverageContext(max_leverage=Leverage.parse("2")),
    )
    request = _risk_request(
        RequestContext(
            pair=pair,
            stake=StakeAmount(Decimal(25)),
            requested_leverage=leverage_decision.leverage.value,
            max_leverage=Leverage.parse("2"),
        ),
    )

    # When
    quote = quote_order(request)

    # Then
    assert leverage_decision.leverage == Leverage.parse("2")
    assert leverage_decision.reason is X7LeverageReason.CAPPED
    assert quote == AcceptedOrderQuote(
        pair=pair,
        side=PositionSide.LONG,
        stake=StakeAmount(Decimal(25)),
        leverage=Leverage.parse("2"),
        adjusted=False,
        reason=None,
    )


def test_x7_order_filled_snapshot_preserves_order_trade_identity() -> None:
    # Given
    pair = TradingPair.parse("ETH/USDT:USDT", TradingMode.FUTURES)
    order = StrategyOrder(order_id=OrderId("order-1"), pair=pair, side=PositionSide.SHORT)
    trade = StrategyTrade(trade_id=TradeId("trade-1"), pair=pair, side=PositionSide.SHORT)

    # When
    snapshot = build_x7_order_filled_snapshot(order=order, trade=trade)

    # Then
    assert snapshot.order_id == "order-1"
    assert snapshot.trade_id == "trade-1"
    assert snapshot.pair == pair
    assert snapshot.side is PositionSide.SHORT
    assert snapshot.pair_and_side_match is True


def test_x7_position_adjustment_is_disabled_without_explicit_bounded_context() -> None:
    # Given
    pair = TradingPair.parse("ETH/USDT:USDT", TradingMode.FUTURES)
    trade = StrategyTrade(trade_id=TradeId("trade-2"), pair=pair, side=PositionSide.LONG)

    # When
    decision = build_x7_position_adjustment_decision(
        X7PositionAdjustmentContext(trade=trade),
    )

    # Then
    assert decision.stake is None
    assert decision.reason is X7PositionAdjustmentReason.NO_ADJUSTMENT
    assert decision.capped is False


def test_x7_position_adjustment_caps_to_available_balance() -> None:
    # Given
    pair = TradingPair.parse("ETH/USDT:USDT", TradingMode.FUTURES)
    trade = StrategyTrade(trade_id=TradeId("trade-3"), pair=pair, side=PositionSide.LONG)

    # When
    decision = build_x7_position_adjustment_decision(
        X7PositionAdjustmentContext(
            trade=trade,
            proposed_stake=StakeAmount(Decimal(50)),
            max_adjustment=StakeAmount(Decimal(40)),
            available_balance=StakeAmount(Decimal(25)),
        ),
    )

    # Then
    assert decision.stake == StakeAmount(Decimal(25))
    assert decision.reason is X7PositionAdjustmentReason.CAPPED_BY_AVAILABLE
    assert decision.capped is True


@dataclass(frozen=True, slots=True)
class RequestContext:
    pair: TradingPair
    stake: StakeAmount
    requested_leverage: Decimal
    max_leverage: Leverage


def _risk_request(context: RequestContext) -> RiskRequest:
    return RiskRequest(
        pair=context.pair,
        side=PositionSide.LONG,
        stake=context.stake,
        requested_leverage=context.requested_leverage,
        account=AccountSnapshot(
            captured_at=NOW,
            equity=StakeAmount(Decimal(1000)),
            available=StakeAmount(Decimal(100)),
            positions=(),
        ),
        policy=RiskPolicy(
            trading_mode=TradingMode.FUTURES,
            max_open_trades=3,
            max_leverage=context.max_leverage,
            stoploss_pct=Decimal("0.10"),
            minimal_roi=Decimal("0.03"),
            paper_trading=True,
            testnet=True,
            live_trading=False,
        ),
        pair_locks=(),
        cooldown_until=None,
        current_time=NOW,
    )
