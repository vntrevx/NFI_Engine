from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class ValidationErrorCode(StrEnum):
    WALK_FORWARD_SPLIT_COUNT_INVALID = "WALK_FORWARD_SPLIT_COUNT_INVALID"
    WALK_FORWARD_SPLIT_OVERLAP = "WALK_FORWARD_SPLIT_OVERLAP"


@dataclass(frozen=True, slots=True)
class ValidationError(Exception):
    code: ValidationErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
