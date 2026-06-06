from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final

APPROVED_CAPABILITIES: Final = (
    "data_provider",
    "typed_config_view",
    "trade_snapshot",
    "order_snapshot",
    "callback_context",
)


@unique
class SandboxViolationKind(StrEnum):
    DIRECT_EXCHANGE_ACCESS = "direct_exchange_access"
    ENV_READ = "env_read"
    FILESYSTEM_WRITE = "filesystem_write"
    NETWORK = "network"
    SUBPROCESS = "subprocess"


@dataclass(frozen=True, slots=True)
class SandboxViolation:
    kind: SandboxViolationKind
    message: str
    line: int


@dataclass(frozen=True, slots=True)
class SandboxCheckResult:
    strategy_spec: str
    passed: bool
    approved_capabilities: tuple[str, ...]
    violations: tuple[SandboxViolation, ...]
    detected_callbacks: tuple[str, ...] = ()
