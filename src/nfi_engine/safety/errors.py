from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class SafetyErrorCode(StrEnum):
    LIVE_TRADING_OUT_OF_SCOPE = "LIVE_TRADING_OUT_OF_SCOPE"


@dataclass(frozen=True, slots=True)
class SafetyError(Exception):
    code: SafetyErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
