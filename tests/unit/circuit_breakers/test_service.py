from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Final

import pytest

from nfi_engine.circuit_breakers import (
    CircuitBreakerDecision,
    CircuitBreakerError,
    CircuitBreakerErrorCode,
    CircuitBreakerKind,
    CircuitBreakerPolicy,
    CircuitBreakerSnapshot,
    circuit_breaker_event,
    ensure_order_intent_allowed,
    evaluate_circuit_breakers,
)

NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)
ZERO: Final = Decimal(0)
ONE_THOUSAND: Final = Decimal(1000)


@dataclass(frozen=True, slots=True)
class SnapshotOverrides:
    realized_pnl_today: Decimal = ZERO
    equity_current: Decimal = ONE_THOUSAND
    consecutive_losses: int = 0
    latest_tick_at: datetime = NOW
    current_time: datetime | None = None
    api_error_count: int = 0
    observed_slippage_pct: Decimal = ZERO
    funding_rate: Decimal = ZERO
    manual_halt: bool = False
    rejected_order_count: int = 0


def test_daily_loss_breaker_halts_order_intents() -> None:
    # Given
    snapshot = _snapshot(SnapshotOverrides(realized_pnl_today=Decimal(-51)))

    # When
    decision = evaluate_circuit_breakers(policy=_policy(), snapshot=snapshot)

    # Then
    assert _first_kind(decision) is CircuitBreakerKind.DAILY_LOSS
    assert decision.trading_halted is True
    assert decision.new_orders_blocked is True


def test_drawdown_breaker_halts_when_equity_drops_below_threshold() -> None:
    # Given
    snapshot = _snapshot(SnapshotOverrides(equity_current=Decimal(850)))

    # When
    decision = evaluate_circuit_breakers(policy=_policy(), snapshot=snapshot)

    # Then
    assert _first_kind(decision) is CircuitBreakerKind.DRAWDOWN


def test_loss_streak_breaker_halts_after_consecutive_losses() -> None:
    # Given
    snapshot = _snapshot(SnapshotOverrides(consecutive_losses=3))

    # When
    decision = evaluate_circuit_breakers(policy=_policy(), snapshot=snapshot)

    # Then
    assert _first_kind(decision) is CircuitBreakerKind.LOSS_STREAK


def test_stale_data_breaker_halts_when_tick_stream_is_old() -> None:
    # Given
    snapshot = _snapshot(SnapshotOverrides(current_time=NOW + timedelta(seconds=90)))

    # When
    decision = evaluate_circuit_breakers(policy=_policy(), snapshot=snapshot)

    # Then
    assert _first_kind(decision) is CircuitBreakerKind.STALE_DATA


def test_api_error_burst_breaker_halts_after_error_threshold() -> None:
    # Given
    snapshot = _snapshot(SnapshotOverrides(api_error_count=5))

    # When
    decision = evaluate_circuit_breakers(policy=_policy(), snapshot=snapshot)

    # Then
    assert _first_kind(decision) is CircuitBreakerKind.API_ERROR_BURST


def test_abnormal_slippage_breaker_halts_after_slippage_threshold() -> None:
    # Given
    snapshot = _snapshot(SnapshotOverrides(observed_slippage_pct=Decimal("0.04")))

    # When
    decision = evaluate_circuit_breakers(policy=_policy(), snapshot=snapshot)

    # Then
    assert _first_kind(decision) is CircuitBreakerKind.ABNORMAL_SLIPPAGE


def test_funding_rate_breaker_halts_after_abs_funding_threshold() -> None:
    # Given
    snapshot = _snapshot(SnapshotOverrides(funding_rate=Decimal("-0.02")))

    # When
    decision = evaluate_circuit_breakers(policy=_policy(), snapshot=snapshot)

    # Then
    assert _first_kind(decision) is CircuitBreakerKind.FUNDING_RATE_ANOMALY


def test_manual_halt_breaker_halts_when_flag_is_set() -> None:
    # Given
    snapshot = _snapshot(SnapshotOverrides(manual_halt=True))

    # When
    decision = evaluate_circuit_breakers(policy=_policy(), snapshot=snapshot)

    # Then
    assert _first_kind(decision) is CircuitBreakerKind.MANUAL_HALT


def test_rejected_order_burst_breaker_halts_after_rejection_threshold() -> None:
    # Given
    snapshot = _snapshot(SnapshotOverrides(rejected_order_count=3))

    # When
    decision = evaluate_circuit_breakers(policy=_policy(), snapshot=snapshot)

    # Then
    assert _first_kind(decision) is CircuitBreakerKind.REJECTED_ORDER_BURST


def test_breaker_resets_when_snapshot_returns_inside_policy() -> None:
    # Given
    triggered = evaluate_circuit_breakers(
        policy=_policy(),
        snapshot=_snapshot(SnapshotOverrides(realized_pnl_today=Decimal(-51))),
    )

    # When
    recovered = evaluate_circuit_breakers(policy=_policy(), snapshot=_snapshot())

    # Then
    assert triggered.trading_halted is True
    assert recovered.trading_halted is False
    assert recovered.triggered == ()


def test_circuit_breaker_event_uses_typed_event_code() -> None:
    # Given
    decision = evaluate_circuit_breakers(
        policy=_policy(),
        snapshot=_snapshot(SnapshotOverrides(realized_pnl_today=Decimal(-51))),
    )

    # When
    event = circuit_breaker_event(
        decision=decision,
        at=NOW,
        correlation_id="corr-test",
        command="unit",
    )

    # Then
    assert event is not None
    assert event.safe_summary == "trading halted by circuit breaker: daily_loss"


def test_halted_decision_rejects_order_intent_before_exchange_placement() -> None:
    # Given
    decision = evaluate_circuit_breakers(
        policy=_policy(),
        snapshot=_snapshot(SnapshotOverrides(realized_pnl_today=Decimal(-51))),
    )

    # When/Then
    with pytest.raises(CircuitBreakerError) as exc_info:
        ensure_order_intent_allowed(decision)
    assert exc_info.value.code is CircuitBreakerErrorCode.CIRCUIT_BREAKER_ACTIVE


def _first_kind(decision: CircuitBreakerDecision) -> CircuitBreakerKind:
    assert len(decision.triggered) > 0
    return decision.triggered[0].kind


def _policy() -> CircuitBreakerPolicy:
    return CircuitBreakerPolicy(
        enabled=True,
        max_daily_loss_usdt=Decimal(50),
        max_drawdown_pct=Decimal("0.10"),
        max_consecutive_losses=3,
        max_stale_seconds=60,
        max_api_errors=5,
        max_slippage_pct=Decimal("0.03"),
        max_abs_funding_rate=Decimal("0.01"),
        manual_halt=False,
        max_rejected_orders=3,
        emergency_exit_enabled=False,
    )


def _snapshot(overrides: SnapshotOverrides | None = None) -> CircuitBreakerSnapshot:
    values = SnapshotOverrides() if overrides is None else overrides
    effective_current_time = (
        NOW + timedelta(seconds=10) if values.current_time is None else values.current_time
    )
    return CircuitBreakerSnapshot(
        realized_pnl_today=values.realized_pnl_today,
        equity_start=ONE_THOUSAND,
        equity_current=values.equity_current,
        consecutive_losses=values.consecutive_losses,
        latest_tick_at=values.latest_tick_at,
        current_time=effective_current_time,
        api_error_count=values.api_error_count,
        observed_slippage_pct=values.observed_slippage_pct,
        funding_rate=values.funding_rate,
        manual_halt=values.manual_halt,
        rejected_order_count=values.rejected_order_count,
    )
