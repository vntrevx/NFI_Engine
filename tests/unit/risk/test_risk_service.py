from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Final

from nfi_engine.domain import (
    AccountSnapshot,
    Leverage,
    LiquidationBuffer,
    Position,
    PositionSide,
    Price,
    Quantity,
    StakeAmount,
    TradeId,
    TradeState,
    TradingMode,
    TradingPair,
)
from nfi_engine.risk import (
    AcceptedOrderQuote,
    ExitDecision,
    PairLock,
    RejectedOrderQuote,
    RiskPolicy,
    RiskRejectionCode,
    RiskRequest,
    evaluate_roi,
    evaluate_stoploss,
    quote_order,
)

NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)


def test_quote_order_rejects_when_stake_exceeds_available_balance() -> None:
    # Given
    request = _request(
        RequestOverrides(stake=Decimal(100), account=_account(available=Decimal(50))),
    )

    # When
    quote = quote_order(request)

    # Then
    assert quote == RejectedOrderQuote(
        code=RiskRejectionCode.STAKE_EXCEEDS_AVAILABLE,
        message="stake exceeds available balance",
    )


def test_quote_order_rejects_when_max_open_trades_is_reached() -> None:
    # Given
    account = _account(
        available=Decimal(1000),
        positions=(_position("open-a"), _position("open-b")),
    )
    policy = _policy(PolicyOverrides(max_open_trades=2))
    request = _request(RequestOverrides(stake=Decimal(100), account=account, policy=policy))

    # When
    quote = quote_order(request)

    # Then
    assert quote == RejectedOrderQuote(
        code=RiskRejectionCode.MAX_OPEN_TRADES,
        message="max open trades reached",
    )


def test_quote_order_rejects_pair_locks_and_cooldowns() -> None:
    # Given
    locked_request = _request(
        RequestOverrides(
            stake=Decimal(100),
            pair_locks=(PairLock(pair=_spot_pair(), reason="manual lock", expires_at=NOW),),
        ),
    )
    cooldown_request = _request(
        RequestOverrides(stake=Decimal(100), cooldown_until=NOW + timedelta(minutes=5)),
    )

    # When
    locked_quote = quote_order(locked_request)
    cooldown_quote = quote_order(cooldown_request)

    # Then
    assert locked_quote == RejectedOrderQuote(
        code=RiskRejectionCode.PAIR_LOCKED,
        message="pair is locked: manual lock",
    )
    assert cooldown_quote == RejectedOrderQuote(
        code=RiskRejectionCode.COOLDOWN_ACTIVE,
        message="pair cooldown active",
    )


def test_quote_order_enforces_spot_long_only_and_live_order_guard() -> None:
    # Given
    spot_short = _request(RequestOverrides(stake=Decimal(100), side=PositionSide.SHORT))
    live_request = _request(
        RequestOverrides(
            stake=Decimal(100),
            policy=_policy(
                PolicyOverrides(paper_trading=False, testnet=False, live_trading=True),
            ),
        ),
    )

    # When
    short_quote = quote_order(spot_short)
    live_quote = quote_order(live_request)

    # Then
    assert short_quote == RejectedOrderQuote(
        code=RiskRejectionCode.SIDE_NOT_ALLOWED,
        message="spot trading only supports long order intents",
    )
    assert live_quote == RejectedOrderQuote(
        code=RiskRejectionCode.REAL_LIVE_ORDER_DISABLED,
        message="real live orders are disabled in milestone 1",
    )


def test_quote_order_caps_futures_leverage_when_requested_above_configured_max() -> None:
    # Given
    policy = _policy(
        PolicyOverrides(trading_mode=TradingMode.FUTURES, max_leverage=Decimal(3)),
    )
    request = _request(
        RequestOverrides(
            pair=TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
            side=PositionSide.SHORT,
            stake=Decimal(100),
            requested_leverage=Decimal(999),
            policy=policy,
        ),
    )

    # When
    quote = quote_order(request)

    # Then
    assert quote == AcceptedOrderQuote(
        pair=TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
        side=PositionSide.SHORT,
        stake=StakeAmount(Decimal(100)),
        leverage=Leverage.parse("3"),
        adjusted=True,
        reason="LEVERAGE_CAPPED",
    )


def test_stoploss_and_roi_exit_decisions_are_deterministic() -> None:
    # Given
    long_position = _position("long-stop")
    short_position = _position("short-roi", side=PositionSide.SHORT, leverage=Decimal(2))

    # When
    stoploss = evaluate_stoploss(
        position=long_position,
        current_price=Price(Decimal(89)),
        stoploss_pct=Decimal("0.10"),
    )
    roi = evaluate_roi(
        position=short_position,
        current_price=Price(Decimal(80)),
        minimal_roi=Decimal("0.10"),
    )

    # Then
    assert stoploss == ExitDecision(should_exit=True, reason="STOPLOSS")
    assert roi == ExitDecision(should_exit=True, reason="ROI")


@dataclass(frozen=True, slots=True)
class RequestOverrides:
    stake: Decimal
    pair: TradingPair | None = None
    side: PositionSide = PositionSide.LONG
    requested_leverage: Decimal | None = None
    account: AccountSnapshot | None = None
    policy: RiskPolicy | None = None
    pair_locks: tuple[PairLock, ...] = ()
    cooldown_until: datetime | None = None


@dataclass(frozen=True, slots=True)
class PolicyOverrides:
    trading_mode: TradingMode = TradingMode.SPOT
    max_open_trades: int = 3
    max_leverage: Decimal | None = None
    paper_trading: bool = True
    testnet: bool = True
    live_trading: bool = False


def _request(overrides: RequestOverrides) -> RiskRequest:
    resolved_policy = _policy(PolicyOverrides()) if overrides.policy is None else overrides.policy
    return RiskRequest(
        pair=_spot_pair() if overrides.pair is None else overrides.pair,
        side=overrides.side,
        stake=StakeAmount(overrides.stake),
        requested_leverage=(
            Decimal(1) if overrides.requested_leverage is None else overrides.requested_leverage
        ),
        account=(
            _account(available=Decimal(1000)) if overrides.account is None else overrides.account
        ),
        policy=resolved_policy,
        pair_locks=overrides.pair_locks,
        cooldown_until=overrides.cooldown_until,
        current_time=NOW,
    )


def _policy(overrides: PolicyOverrides) -> RiskPolicy:
    return RiskPolicy(
        trading_mode=overrides.trading_mode,
        max_open_trades=overrides.max_open_trades,
        max_leverage=(
            Leverage.parse("5")
            if overrides.max_leverage is None
            else Leverage.parse(overrides.max_leverage)
        ),
        stoploss_pct=Decimal("0.10"),
        minimal_roi=Decimal("0.03"),
        paper_trading=overrides.paper_trading,
        testnet=overrides.testnet,
        live_trading=overrides.live_trading,
    )


def _account(
    *,
    available: Decimal,
    positions: tuple[Position, ...] = (),
) -> AccountSnapshot:
    return AccountSnapshot(
        captured_at=NOW,
        equity=StakeAmount(Decimal(1000)),
        available=StakeAmount(available),
        positions=positions,
    )


def _position(
    trade_id: str,
    *,
    side: PositionSide = PositionSide.LONG,
    leverage: Decimal | None = None,
) -> Position:
    resolved_leverage = Decimal(1) if leverage is None else leverage
    return Position(
        trade_id=TradeId(trade_id),
        pair=_spot_pair(),
        side=side,
        quantity=Quantity(Decimal(1)),
        entry_price=Price(Decimal(100)),
        leverage=Leverage.parse(resolved_leverage),
        liquidation_buffer=LiquidationBuffer.parse("0.05"),
        state=TradeState.OPEN,
    )


def _spot_pair() -> TradingPair:
    return TradingPair.parse("BTC/USDT", TradingMode.SPOT)
