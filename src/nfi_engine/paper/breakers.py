from __future__ import annotations

from decimal import Decimal
from typing import Final

from nfi_engine.circuit_breakers import (
    CircuitBreakerDecision,
    CircuitBreakerSnapshot,
    evaluate_circuit_breakers,
)
from nfi_engine.circuit_breakers import (
    policy_from_runtime as circuit_policy_from_runtime,
)
from nfi_engine.domain import StakeAmount
from nfi_engine.paper.models import PaperRunRequest, PaperTick

ZERO: Final = Decimal(0)


def breaker_decision(
    *,
    request: PaperRunRequest,
    previous_tick: PaperTick | None,
    current_tick: PaperTick,
) -> CircuitBreakerDecision:
    latest_tick_at = current_tick.at if previous_tick is None else previous_tick.at
    return evaluate_circuit_breakers(
        policy=circuit_policy_from_runtime(request.settings),
        snapshot=CircuitBreakerSnapshot(
            realized_pnl_today=ZERO,
            equity_start=StakeAmount(Decimal(1000)),
            equity_current=StakeAmount(Decimal(1000)),
            consecutive_losses=0,
            latest_tick_at=latest_tick_at,
            current_time=current_tick.at,
            api_error_count=0,
            observed_slippage_pct=ZERO,
            funding_rate=ZERO,
            manual_halt=False,
            rejected_order_count=0,
        ),
    )


def trading_halted(decision: CircuitBreakerDecision | None) -> bool:
    if decision is None:
        return False
    return decision.trading_halted


def first_breaker(decision: CircuitBreakerDecision | None) -> str | None:
    if decision is None:
        return None
    if len(decision.triggered) == 0:
        return None
    return decision.triggered[0].kind.value


def protection_reasons(decision: CircuitBreakerDecision) -> tuple[str, ...]:
    return tuple(trigger.kind.value for trigger in decision.triggered)
