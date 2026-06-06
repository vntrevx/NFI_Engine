from __future__ import annotations

from datetime import datetime

from nfi_engine.circuit_breakers.models import CircuitBreakerDecision
from nfi_engine.events import EventCode, EventSeverity, TradingEvent


def circuit_breaker_event(
    *,
    decision: CircuitBreakerDecision,
    at: datetime,
    correlation_id: str,
    command: str,
) -> TradingEvent | None:
    if not decision.trading_halted:
        return None
    breaker = decision.triggered[0].kind.value
    return TradingEvent(
        at=at,
        severity=EventSeverity.ERROR,
        code=EventCode.CIRCUIT_BREAKER_TRIGGERED,
        correlation_id=correlation_id,
        command=command,
        route=None,
        safe_summary=f"trading halted by circuit breaker: {breaker}",
        report_hint="attach circuit breaker output and recent paper-run event logs",
    )
