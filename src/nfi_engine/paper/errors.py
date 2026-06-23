from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class PaperErrorCode(StrEnum):
    LIVE_EXCHANGE_DISABLED_FOR_MILESTONE = "LIVE_EXCHANGE_DISABLED_FOR_MILESTONE"
    PREFLIGHT_BLOCKED = "PREFLIGHT_BLOCKED"
    TICK_PARSE_ERROR = "TICK_PARSE_ERROR"
    WALLET_BALANCE_UNAVAILABLE = "WALLET_BALANCE_UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class PaperError(Exception):
    code: PaperErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
