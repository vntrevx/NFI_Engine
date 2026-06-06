from __future__ import annotations

from decimal import Decimal

from nfi_engine.circuit_breakers.errors import CircuitBreakerError, CircuitBreakerErrorCode
from nfi_engine.circuit_breakers.models import (
    CircuitBreakerDecision,
    CircuitBreakerKind,
    CircuitBreakerPolicy,
    CircuitBreakerSnapshot,
    CircuitBreakerTrigger,
)

ZERO: Decimal = Decimal(0)


def evaluate_circuit_breakers(
    *,
    policy: CircuitBreakerPolicy,
    snapshot: CircuitBreakerSnapshot,
) -> CircuitBreakerDecision:
    if not policy.enabled:
        return _decision(())
    triggers = tuple(_triggers(policy=policy, snapshot=snapshot))
    return _decision(triggers, emergency_exit_enabled=policy.emergency_exit_enabled)


def ensure_order_intent_allowed(decision: CircuitBreakerDecision) -> None:
    if not decision.new_orders_blocked:
        return
    raise CircuitBreakerError(
        code=CircuitBreakerErrorCode.CIRCUIT_BREAKER_ACTIVE,
        message=f"new orders blocked by circuit breaker: {_first_breaker(decision)}",
    )


def _triggers(
    *,
    policy: CircuitBreakerPolicy,
    snapshot: CircuitBreakerSnapshot,
) -> tuple[CircuitBreakerTrigger, ...]:
    triggers: tuple[CircuitBreakerTrigger, ...] = ()
    daily_loss = -snapshot.realized_pnl_today
    if daily_loss >= policy.max_daily_loss_usdt:
        triggers += (_trigger(CircuitBreakerKind.DAILY_LOSS, "daily realized loss exceeded"),)
    drawdown = _drawdown_pct(snapshot)
    if drawdown >= policy.max_drawdown_pct:
        triggers += (_trigger(CircuitBreakerKind.DRAWDOWN, "equity drawdown exceeded"),)
    if snapshot.consecutive_losses >= policy.max_consecutive_losses:
        triggers += (_trigger(CircuitBreakerKind.LOSS_STREAK, "loss streak exceeded"),)
    stale_seconds = (snapshot.current_time - snapshot.latest_tick_at).total_seconds()
    if stale_seconds > policy.max_stale_seconds:
        triggers += (_trigger(CircuitBreakerKind.STALE_DATA, "market data stream is stale"),)
    if snapshot.api_error_count >= policy.max_api_errors:
        triggers += (_trigger(CircuitBreakerKind.API_ERROR_BURST, "exchange api error burst"),)
    if abs(snapshot.observed_slippage_pct) >= policy.max_slippage_pct:
        triggers += (_trigger(CircuitBreakerKind.ABNORMAL_SLIPPAGE, "slippage exceeded"),)
    if abs(snapshot.funding_rate) >= policy.max_abs_funding_rate:
        triggers += (_trigger(CircuitBreakerKind.FUNDING_RATE_ANOMALY, "funding rate anomaly"),)
    if policy.manual_halt or snapshot.manual_halt:
        triggers += (_trigger(CircuitBreakerKind.MANUAL_HALT, "manual halt is active"),)
    if snapshot.rejected_order_count >= policy.max_rejected_orders:
        triggers += (_trigger(CircuitBreakerKind.REJECTED_ORDER_BURST, "order rejection burst"),)
    return triggers


def _drawdown_pct(snapshot: CircuitBreakerSnapshot) -> Decimal:
    if snapshot.equity_start <= ZERO:
        return ZERO
    return (snapshot.equity_start - snapshot.equity_current) / snapshot.equity_start


def _decision(
    triggers: tuple[CircuitBreakerTrigger, ...],
    *,
    emergency_exit_enabled: bool = False,
) -> CircuitBreakerDecision:
    halted = len(triggers) > 0
    return CircuitBreakerDecision(
        trading_halted=halted,
        new_orders_blocked=halted,
        emergency_exit=halted and emergency_exit_enabled,
        triggered=triggers,
    )


def _trigger(kind: CircuitBreakerKind, message: str) -> CircuitBreakerTrigger:
    return CircuitBreakerTrigger(kind=kind, message=message)


def _first_breaker(decision: CircuitBreakerDecision) -> str:
    if len(decision.triggered) == 0:
        return "none"
    return decision.triggered[0].kind.value
