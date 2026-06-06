from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class EventLogErrorCode(StrEnum):
    EVENT_LOG_PARSE_ERROR = "EVENT_LOG_PARSE_ERROR"


@dataclass(frozen=True, slots=True)
class EventLogError(Exception):
    code: EventLogErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
