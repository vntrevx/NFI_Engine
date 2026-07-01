from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique

from nfi_engine.runtime_health.models import RuntimeHealthState


@unique
class RestrictedLivePilotCode(StrEnum):
    DISABLED = "LIVE_PILOT_DISABLED"
    CANARY_MARKER = "LIVE_PILOT_CANARY_PASS_MARKER"
    REQUIRED_FIELDS = "LIVE_PILOT_REQUIRED_FIELDS"
    FRESHNESS = "LIVE_PILOT_FRESHNESS"
    BREAKER = "LIVE_PILOT_BREAKER"
    READY = "LIVE_PILOT_READY"


@dataclass(frozen=True, slots=True)
class RestrictedLivePilotStatus:
    enabled: bool
    state: RuntimeHealthState
    code: RestrictedLivePilotCode
    message: str
    next_action: str
    canary_pass_marker_path: str | None
    pair_allowlist: tuple[str, ...]
