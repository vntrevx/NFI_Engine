from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, unique
from typing import Final

from nfi_engine.circuit_breakers import CircuitBreakerDecision
from nfi_engine.domain import PositionSide, TradingPair
from nfi_engine.risk import PairLock

ZERO_ACTIONS: Final = 0


@unique
class X7ProtectionReason(StrEnum):
    CLEAR = "PROTECTION_CLEAR"
    PAIR_LOCKED = "PAIR_LOCKED"
    COOLDOWN_ACTIVE = "COOLDOWN_ACTIVE"
    STALE_DATA = "STALE_DATA"
    CIRCUIT_BREAKER_BLOCKED = "CIRCUIT_BREAKER_BLOCKED"
    LIVE_CONFIRMATION_REQUIRED = "LIVE_CONFIRMATION_REQUIRED"


@unique
class X7LoopHookReason(StrEnum):
    IDLE = "LOOP_IDLE"
    ACCEPTED = "LOOP_ACCEPTED"
    BOUNDED = "LOOP_BOUNDED"


@dataclass(frozen=True, slots=True)
class X7ProtectionGuard:
    reason: X7ProtectionReason
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class X7PairLockGuardContext:
    pair: TradingPair
    pair_locks: tuple[PairLock, ...]
    current_time: datetime


@dataclass(frozen=True, slots=True)
class X7CooldownGuardContext:
    cooldown_until: datetime | None
    current_time: datetime


@dataclass(frozen=True, slots=True)
class X7StaleDataGuardContext:
    latest_data_at: datetime
    current_time: datetime
    max_stale_seconds: int


@dataclass(frozen=True, slots=True)
class X7TradeConfirmationContext:
    pair: TradingPair
    side: PositionSide
    guards: tuple[X7ProtectionGuard, ...] = ()
    live_trading: bool = False
    live_confirmed: bool = False


@dataclass(frozen=True, slots=True)
class X7TradeConfirmationDecision:
    allowed: bool
    reason: X7ProtectionReason
    detail: str | None = None


@dataclass(frozen=True, slots=True)
class X7LoopHookContext:
    requested_actions: int = ZERO_ACTIONS
    max_actions: int = ZERO_ACTIONS


@dataclass(frozen=True, slots=True)
class X7LoopHookDecision:
    allowed_actions: int
    reason: X7LoopHookReason
    hidden_network_io: bool
    mutates_raw_config: bool


def build_x7_pair_lock_guard(context: X7PairLockGuardContext) -> X7ProtectionGuard | None:
    for pair_lock in context.pair_locks:
        if pair_lock.pair == context.pair and pair_lock.expires_at >= context.current_time:
            return X7ProtectionGuard(
                reason=X7ProtectionReason.PAIR_LOCKED,
                detail=pair_lock.reason,
            )
    return None


def build_x7_cooldown_guard(context: X7CooldownGuardContext) -> X7ProtectionGuard | None:
    cooldown_until = context.cooldown_until
    if cooldown_until is None or cooldown_until <= context.current_time:
        return None
    return X7ProtectionGuard(reason=X7ProtectionReason.COOLDOWN_ACTIVE)


def build_x7_stale_data_guard(context: X7StaleDataGuardContext) -> X7ProtectionGuard | None:
    stale_seconds = (context.current_time - context.latest_data_at).total_seconds()
    if context.max_stale_seconds <= ZERO_ACTIONS or stale_seconds <= context.max_stale_seconds:
        return None
    return X7ProtectionGuard(
        reason=X7ProtectionReason.STALE_DATA,
        detail=str(int(stale_seconds)),
    )


def build_x7_circuit_breaker_guard(
    decision: CircuitBreakerDecision,
) -> X7ProtectionGuard | None:
    if not decision.new_orders_blocked:
        return None
    return X7ProtectionGuard(
        reason=X7ProtectionReason.CIRCUIT_BREAKER_BLOCKED,
        detail=_first_circuit_breaker(decision),
    )


def build_x7_trade_confirmation_decision(
    context: X7TradeConfirmationContext,
) -> X7TradeConfirmationDecision:
    first_guard = _first_guard(context.guards)
    if first_guard is not None:
        return X7TradeConfirmationDecision(
            allowed=False,
            reason=first_guard.reason,
            detail=first_guard.detail,
        )
    if context.live_trading and not context.live_confirmed:
        return X7TradeConfirmationDecision(
            allowed=False,
            reason=X7ProtectionReason.LIVE_CONFIRMATION_REQUIRED,
        )
    return X7TradeConfirmationDecision(allowed=True, reason=X7ProtectionReason.CLEAR)


def build_x7_loop_hook_decision(context: X7LoopHookContext) -> X7LoopHookDecision:
    if context.requested_actions <= ZERO_ACTIONS or context.max_actions <= ZERO_ACTIONS:
        return X7LoopHookDecision(
            allowed_actions=ZERO_ACTIONS,
            reason=X7LoopHookReason.IDLE,
            hidden_network_io=False,
            mutates_raw_config=False,
        )
    allowed_actions = min(context.requested_actions, context.max_actions)
    reason = (
        X7LoopHookReason.BOUNDED
        if allowed_actions < context.requested_actions
        else X7LoopHookReason.ACCEPTED
    )
    return X7LoopHookDecision(
        allowed_actions=allowed_actions,
        reason=reason,
        hidden_network_io=False,
        mutates_raw_config=False,
    )


def _first_guard(guards: tuple[X7ProtectionGuard, ...]) -> X7ProtectionGuard | None:
    if len(guards) == 0:
        return None
    return guards[0]


def _first_circuit_breaker(decision: CircuitBreakerDecision) -> str | None:
    if len(decision.triggered) == 0:
        return None
    return decision.triggered[0].kind.value
