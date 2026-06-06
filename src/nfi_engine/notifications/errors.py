from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class NotificationErrorCode(StrEnum):
    NOTIFICATION_ADAPTER_FAILED = "notification_adapter_failed"
    NOTIFICATION_CONFIG_INVALID = "notification_config_invalid"
    NOTIFICATION_HTTP_ERROR = "notification_http_error"
    NOTIFICATION_TIMEOUT = "notification_timeout"


@dataclass(frozen=True, slots=True)
class NotificationError(Exception):
    code: NotificationErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
