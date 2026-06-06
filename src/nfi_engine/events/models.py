from __future__ import annotations

from datetime import datetime
from enum import StrEnum, unique
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


@unique
class EventSeverity(StrEnum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@unique
class EventCode(StrEnum):
    API_STARTED = "API_STARTED"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    CIRCUIT_BREAKER_TRIGGERED = "CIRCUIT_BREAKER_TRIGGERED"
    CONFIG_VALIDATION_ERROR = "CONFIG_VALIDATION_ERROR"
    NOTIFICATION_TEST = "NOTIFICATION_TEST"


class TradingEvent(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    at: datetime
    severity: EventSeverity
    code: EventCode
    correlation_id: str
    command: str | None
    route: str | None
    safe_summary: str
    report_hint: str
