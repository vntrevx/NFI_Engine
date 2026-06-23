from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique

from nfi_engine.config import RuntimeSettings
from nfi_engine.paper import BotCommand, BotState
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.runtime_health import RuntimeHealthSnapshot, RuntimeHealthState


@unique
class RuntimeControlCode(StrEnum):
    RUNTIME_CONTROL_ACCEPTED = "RUNTIME_CONTROL_ACCEPTED"
    RUNTIME_ALREADY_PAUSED = "RUNTIME_ALREADY_PAUSED"
    RUNTIME_ALREADY_STOPPED = "RUNTIME_ALREADY_STOPPED"
    RUNTIME_ALREADY_RUNNING = "RUNTIME_ALREADY_RUNNING"
    RUNTIME_INVALID_TRANSITION = "RUNTIME_INVALID_TRANSITION"
    RUNTIME_PREFLIGHT_REQUIRED = "RUNTIME_PREFLIGHT_REQUIRED"
    RUNTIME_PREFLIGHT_BLOCKED = "RUNTIME_PREFLIGHT_BLOCKED"
    RUNTIME_HEALTH_REQUIRED = "RUNTIME_HEALTH_REQUIRED"
    RUNTIME_HEALTH_BLOCKED = "RUNTIME_HEALTH_BLOCKED"
    RUNTIME_LIVE_UNSAFE = "RUNTIME_LIVE_UNSAFE"


@dataclass(frozen=True, slots=True)
class RuntimeControlRequest:
    settings: RuntimeSettings
    state: BotState
    command: BotCommand
    readiness: PreflightReport | None
    health: RuntimeHealthSnapshot | None = None


@dataclass(frozen=True, slots=True)
class RuntimeControlResult:
    previous_state: BotState
    state: BotState
    command: BotCommand
    accepted: bool
    code: RuntimeControlCode
    message: str
    new_entries_allowed: bool
    runtime_health_state: RuntimeHealthState | None
    next_action: str
    live_orders_action: str
