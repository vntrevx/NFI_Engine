from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class SandboxErrorCode(StrEnum):
    SANDBOX_STRATEGY_LOAD_ERROR = "SANDBOX_STRATEGY_LOAD_ERROR"
    SANDBOX_VIOLATION = "SANDBOX_VIOLATION"


@dataclass(frozen=True, slots=True)
class SandboxError(Exception):
    code: SandboxErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
