from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique


@unique
class CircuitBreakerKind(StrEnum):
    DAILY_LOSS = "daily_loss"
    DRAWDOWN = "drawdown"
    LOSS_STREAK = "loss_streak"
    STALE_DATA = "stale_data"
    API_ERROR_BURST = "api_error_burst"
    ABNORMAL_SLIPPAGE = "abnormal_slippage"
    FUNDING_RATE_ANOMALY = "funding_rate_anomaly"
    MANUAL_HALT = "manual_halt"
    REJECTED_ORDER_BURST = "rejected_order_burst"


@dataclass(frozen=True, slots=True)
class CircuitBreakerPolicy:
    enabled: bool
    max_daily_loss_usdt: Decimal
    max_drawdown_pct: Decimal
    max_consecutive_losses: int
    max_stale_seconds: int
    max_api_errors: int
    max_slippage_pct: Decimal
    max_abs_funding_rate: Decimal
    manual_halt: bool
    max_rejected_orders: int
    emergency_exit_enabled: bool


@dataclass(frozen=True, slots=True)
class CircuitBreakerSnapshot:
    realized_pnl_today: Decimal
    equity_start: Decimal
    equity_current: Decimal
    consecutive_losses: int
    latest_tick_at: datetime
    current_time: datetime
    api_error_count: int
    observed_slippage_pct: Decimal
    funding_rate: Decimal
    manual_halt: bool
    rejected_order_count: int


@dataclass(frozen=True, slots=True)
class CircuitBreakerTrigger:
    kind: CircuitBreakerKind
    message: str


@dataclass(frozen=True, slots=True)
class CircuitBreakerDecision:
    trading_halted: bool
    new_orders_blocked: bool
    emergency_exit: bool
    triggered: tuple[CircuitBreakerTrigger, ...]
