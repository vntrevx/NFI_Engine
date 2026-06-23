from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Final

from nfi_engine.circuit_breakers import (
    CircuitBreakerDecision,
    CircuitBreakerKind,
    CircuitBreakerTrigger,
)
from nfi_engine.domain import PositionSide, TradingMode, TradingPair
from nfi_engine.risk import PairLock
from nfi_engine.strategy import FreqtradeStrategyAdapter
from nfi_engine.strategy.nfi_x7 import (
    X7CooldownGuardContext,
    X7LoopHookContext,
    X7LoopHookReason,
    X7NativeStrategy,
    X7PairLockGuardContext,
    X7ProtectionReason,
    X7StaleDataGuardContext,
    X7TradeConfirmationContext,
    build_x7_circuit_breaker_guard,
    build_x7_cooldown_guard,
    build_x7_loop_hook_decision,
    build_x7_pair_lock_guard,
    build_x7_stale_data_guard,
    build_x7_trade_confirmation_decision,
)

NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)


def test_x7_protection_guards_emit_stable_machine_reasons() -> None:
    # Given
    pair = _pair()
    pair_lock = PairLock(
        pair=pair,
        reason="operator lock",
        expires_at=NOW + timedelta(minutes=1),
    )
    circuit_decision = CircuitBreakerDecision(
        trading_halted=True,
        new_orders_blocked=True,
        emergency_exit=False,
        triggered=(
            CircuitBreakerTrigger(
                kind=CircuitBreakerKind.STALE_DATA,
                message="market data stream is stale",
            ),
        ),
    )

    # When
    lock_guard = build_x7_pair_lock_guard(
        X7PairLockGuardContext(pair=pair, pair_locks=(pair_lock,), current_time=NOW),
    )
    cooldown_guard = build_x7_cooldown_guard(
        X7CooldownGuardContext(
            cooldown_until=NOW + timedelta(minutes=5),
            current_time=NOW,
        ),
    )
    stale_guard = build_x7_stale_data_guard(
        X7StaleDataGuardContext(
            latest_data_at=NOW - timedelta(minutes=10),
            current_time=NOW,
            max_stale_seconds=300,
        ),
    )
    circuit_guard = build_x7_circuit_breaker_guard(circuit_decision)

    # Then
    assert lock_guard is not None
    assert lock_guard.reason is X7ProtectionReason.PAIR_LOCKED
    assert lock_guard.detail == "operator lock"
    assert cooldown_guard is not None
    assert cooldown_guard.reason is X7ProtectionReason.COOLDOWN_ACTIVE
    assert stale_guard is not None
    assert stale_guard.reason is X7ProtectionReason.STALE_DATA
    assert circuit_guard is not None
    assert circuit_guard.reason is X7ProtectionReason.CIRCUIT_BREAKER_BLOCKED
    assert circuit_guard.detail == CircuitBreakerKind.STALE_DATA.value


def test_x7_trade_confirmation_blocks_guarded_or_unconfirmed_live_actions() -> None:
    # Given
    guard = build_x7_stale_data_guard(
        X7StaleDataGuardContext(
            latest_data_at=NOW - timedelta(minutes=10),
            current_time=NOW,
            max_stale_seconds=60,
        ),
    )
    assert guard is not None

    # When
    guarded = build_x7_trade_confirmation_decision(
        X7TradeConfirmationContext(
            pair=_pair(),
            side=PositionSide.LONG,
            guards=(guard,),
        ),
    )
    live_denied = build_x7_trade_confirmation_decision(
        X7TradeConfirmationContext(
            pair=_pair(),
            side=PositionSide.SHORT,
            live_trading=True,
            live_confirmed=False,
        ),
    )
    dry_allowed = build_x7_trade_confirmation_decision(
        X7TradeConfirmationContext(pair=_pair(), side=PositionSide.LONG),
    )

    # Then
    assert guarded.allowed is False
    assert guarded.reason is X7ProtectionReason.STALE_DATA
    assert live_denied.allowed is False
    assert live_denied.reason is X7ProtectionReason.LIVE_CONFIRMATION_REQUIRED
    assert dry_allowed.allowed is True
    assert dry_allowed.reason is X7ProtectionReason.CLEAR


def test_x7_loop_hook_caps_actions_without_io_or_config_mutation() -> None:
    # Given
    context = X7LoopHookContext(requested_actions=8, max_actions=3)

    # When
    decision = build_x7_loop_hook_decision(context)

    # Then
    assert decision.allowed_actions == 3
    assert decision.reason is X7LoopHookReason.BOUNDED
    assert decision.hidden_network_io is False
    assert decision.mutates_raw_config is False


def test_x7_native_strategy_exposes_confirmation_callbacks() -> None:
    # Given
    strategy = X7NativeStrategy()
    adapter = FreqtradeStrategyAdapter.from_strategy(strategy)

    # When
    inspection = adapter.inspect()
    entry_allowed = strategy.confirm_trade_entry(_pair(), PositionSide.LONG)
    exit_allowed = strategy.confirm_trade_exit(_pair(), PositionSide.LONG)

    # Then
    assert {"confirm_trade_entry", "confirm_trade_exit"}.issubset(
        set(inspection.detected_callbacks),
    )
    assert entry_allowed is True
    assert exit_allowed is True


def test_x7_stale_data_guard_uses_strict_seconds_boundary() -> None:
    # Given
    context = X7StaleDataGuardContext(
        latest_data_at=NOW - timedelta(seconds=300),
        current_time=NOW,
        max_stale_seconds=300,
    )

    # When
    guard = build_x7_stale_data_guard(context)

    # Then
    assert guard is None


def _pair() -> TradingPair:
    return TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
