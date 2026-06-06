from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class CircuitBreakerErrorCode(StrEnum):
    CIRCUIT_BREAKER_ACTIVE = "CIRCUIT_BREAKER_ACTIVE"


@dataclass(frozen=True, slots=True)
class CircuitBreakerError(Exception):
    code: CircuitBreakerErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
