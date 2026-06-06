from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from nfi_engine.domain.enums import ErrorCode


@dataclass(frozen=True, slots=True)
class DomainError(Exception):
    code: ErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
