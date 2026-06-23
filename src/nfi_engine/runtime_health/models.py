from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, unique

from nfi_engine.strategy.nfi_x7 import X7SemanticStatus
from nfi_engine.wallet import WalletBalanceSnapshot


@unique
class RuntimeHealthState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    BLOCKED = "blocked"


@unique
class RuntimeHealthCode(StrEnum):
    ENGINE_HEARTBEAT = "ENGINE_HEARTBEAT"
    PREFLIGHT = "PREFLIGHT"
    WALLET_BALANCE = "WALLET_BALANCE"
    DATA_FRESHNESS = "DATA_FRESHNESS"
    CLOCK_SKEW = "CLOCK_SKEW"
    DISK_BUDGET = "DISK_BUDGET"
    MEMORY_BUDGET = "MEMORY_BUDGET"
    CIRCUIT_BREAKER_STATE = "CIRCUIT_BREAKER_STATE"


@dataclass(frozen=True, slots=True)
class RuntimeHealthCheck:
    code: RuntimeHealthCode
    state: RuntimeHealthState
    message: str
    next_action: str


@dataclass(frozen=True, slots=True)
class RuntimeResourceSnapshot:
    captured_at: datetime
    free_disk_bytes: int
    memory_rss_bytes: int
    disk_state: RuntimeHealthState
    memory_state: RuntimeHealthState


@dataclass(frozen=True, slots=True)
class RuntimeHealthSnapshot:
    generated_at: datetime
    state: RuntimeHealthState
    next_action: str
    checks: tuple[RuntimeHealthCheck, ...]
    resources: RuntimeResourceSnapshot
    wallet_balance: WalletBalanceSnapshot
    x7_semantic_status: X7SemanticStatus
