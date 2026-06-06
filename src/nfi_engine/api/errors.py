from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class ApiErrorCode(StrEnum):
    API_AUTH_REQUIRED = "API_AUTH_REQUIRED"
    API_WEAK_AUTH_VALUE = "WEAK_API_TOKEN"
    API_ROUTE_NOT_FOUND = "API_ROUTE_NOT_FOUND"
    CSRF_TOKEN_REQUIRED = "CSRF_TOKEN_REQUIRED"  # noqa: S105
    CSRF_TOKEN_INVALID = "CSRF_TOKEN_INVALID"  # noqa: S105
    SESSION_EXPIRED = "SESSION_EXPIRED"
    READONLY_ACTION_BLOCKED = "READONLY_ACTION_BLOCKED"
    TICK_PARSE_ERROR = "TICK_PARSE_ERROR"


@dataclass(frozen=True, slots=True)
class ApiConfigurationError(Exception):
    code: ApiErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
