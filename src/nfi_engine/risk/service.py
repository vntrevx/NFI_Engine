from __future__ import annotations

from decimal import Decimal
from typing import assert_never

from nfi_engine.domain import (
    DomainError,
    Leverage,
    OrderIntentDraft,
    OrderType,
    Position,
    PositionSide,
    Price,
    TimeInForce,
    TradeState,
    TradingMode,
    create_order_intent,
)
from nfi_engine.risk.models import (
    AcceptedOrderQuote,
    ExitDecision,
    OrderQuote,
    RejectedOrderQuote,
    RiskRejectionCode,
    RiskRequest,
)

ZERO: Decimal = Decimal(0)
ONE: Decimal = Decimal(1)


def quote_order(request: RiskRequest) -> OrderQuote:
    runtime_rejection = _runtime_rejection(request)
    if runtime_rejection is not None:
        return runtime_rejection
    pair_rejection = _pair_rejection(request)
    if pair_rejection is not None:
        return pair_rejection
    stake_rejection = _stake_rejection(request)
    if stake_rejection is not None:
        return stake_rejection
    capacity_rejection = _capacity_rejection(request)
    if capacity_rejection is not None:
        return capacity_rejection
    side_rejection = _side_rejection(request)
    if side_rejection is not None:
        return side_rejection
    leverage, adjusted, reason = _effective_leverage(request)
    return AcceptedOrderQuote(
        pair=request.pair,
        side=request.side,
        stake=request.stake,
        leverage=leverage,
        adjusted=adjusted,
        reason=reason,
    )


def evaluate_stoploss(
    *,
    position: Position,
    current_price: Price,
    stoploss_pct: Decimal,
) -> ExitDecision:
    threshold = _stoploss_threshold(position=position, stoploss_pct=stoploss_pct)
    match position.side:
        case PositionSide.LONG:
            should_exit = current_price <= threshold
        case PositionSide.SHORT:
            should_exit = current_price >= threshold
        case unreachable:
            assert_never(unreachable)
    return ExitDecision(should_exit=should_exit, reason="STOPLOSS" if should_exit else None)


def evaluate_roi(
    *,
    position: Position,
    current_price: Price,
    minimal_roi: Decimal,
) -> ExitDecision:
    should_exit = _profit_pct(position=position, current_price=current_price) >= minimal_roi
    return ExitDecision(should_exit=should_exit, reason="ROI" if should_exit else None)


def _runtime_rejection(request: RiskRequest) -> RejectedOrderQuote | None:
    if request.policy.paper_trading or request.policy.testnet:
        return None
    if request.policy.live_trading:
        return _rejected(
            RiskRejectionCode.REAL_LIVE_ORDER_DISABLED,
            "real live orders are disabled in milestone 1",
        )
    return _rejected(
        RiskRejectionCode.REAL_LIVE_ORDER_DISABLED,
        "runtime must be paper or testnet in milestone 1",
    )


def _pair_rejection(request: RiskRequest) -> RejectedOrderQuote | None:
    for lock in request.pair_locks:
        if lock.pair == request.pair and lock.expires_at >= request.current_time:
            return _rejected(RiskRejectionCode.PAIR_LOCKED, f"pair is locked: {lock.reason}")
    if request.cooldown_until is not None and request.cooldown_until > request.current_time:
        return _rejected(RiskRejectionCode.COOLDOWN_ACTIVE, "pair cooldown active")
    try:
        request.pair.require_mode(request.policy.trading_mode)
    except DomainError as exc:
        return _rejected(RiskRejectionCode.PAIR_MODE_INVALID, exc.message)
    return None


def _stake_rejection(request: RiskRequest) -> RejectedOrderQuote | None:
    if request.stake <= ZERO:
        return _rejected(RiskRejectionCode.STAKE_OUT_OF_RANGE, "stake must be greater than zero")
    if request.stake > request.account.available:
        return _rejected(
            RiskRejectionCode.STAKE_EXCEEDS_AVAILABLE,
            "stake exceeds available balance",
        )
    return None


def _capacity_rejection(request: RiskRequest) -> RejectedOrderQuote | None:
    open_count = sum(
        1 for position in request.account.positions if position.state is TradeState.OPEN
    )
    if open_count >= request.policy.max_open_trades:
        return _rejected(RiskRejectionCode.MAX_OPEN_TRADES, "max open trades reached")
    return None


def _side_rejection(request: RiskRequest) -> RejectedOrderQuote | None:
    try:
        create_order_intent(
            OrderIntentDraft(
                pair=request.pair,
                trading_mode=request.policy.trading_mode,
                side=request.side,
                order_type=OrderType.MARKET,
                leverage=Leverage.one(),
                time_in_force=TimeInForce.GTC,
            ),
        )
    except DomainError as exc:
        return _rejected(RiskRejectionCode.SIDE_NOT_ALLOWED, exc.message)
    return None


def _effective_leverage(request: RiskRequest) -> tuple[Leverage, bool, str | None]:
    match request.policy.trading_mode:
        case TradingMode.SPOT:
            return Leverage.one(), request.requested_leverage != ONE, "LEVERAGE_IGNORED"
        case TradingMode.FUTURES:
            capped = min(request.requested_leverage, request.policy.max_leverage.value)
            leverage = Leverage.parse(capped)
            adjusted = capped != request.requested_leverage
            return leverage, adjusted, "LEVERAGE_CAPPED" if adjusted else None
        case unreachable:
            assert_never(unreachable)


def _stoploss_threshold(*, position: Position, stoploss_pct: Decimal) -> Decimal:
    match position.side:
        case PositionSide.LONG:
            return position.entry_price * (ONE - stoploss_pct)
        case PositionSide.SHORT:
            return position.entry_price * (ONE + stoploss_pct)
        case unreachable:
            assert_never(unreachable)


def _profit_pct(*, position: Position, current_price: Price) -> Decimal:
    match position.side:
        case PositionSide.LONG:
            raw_profit = (current_price - position.entry_price) / position.entry_price
        case PositionSide.SHORT:
            raw_profit = (position.entry_price - current_price) / position.entry_price
        case unreachable:
            assert_never(unreachable)
    return raw_profit * position.leverage.value


def _rejected(code: RiskRejectionCode, message: str) -> RejectedOrderQuote:
    return RejectedOrderQuote(code=code, message=message)
