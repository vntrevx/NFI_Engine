from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class ExchangeErrorCode(StrEnum):
    CCXT_CLIENT_REQUIRED = "CCXT_CLIENT_REQUIRED"
    EXCHANGE_AUTH_FAILED = "EXCHANGE_AUTH_FAILED"
    EXCHANGE_HTTP_ERROR = "EXCHANGE_HTTP_ERROR"
    EXCHANGE_ID_INVALID = "EXCHANGE_ID_INVALID"
    EXCHANGE_RESPONSE_INVALID = "EXCHANGE_RESPONSE_INVALID"
    LIVE_EXCHANGE_DISABLED_FOR_MILESTONE = "LIVE_EXCHANGE_DISABLED_FOR_MILESTONE"
    ORDER_PAYLOAD_INVALID = "ORDER_PAYLOAD_INVALID"
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    TICK_NOT_FOUND = "TICK_NOT_FOUND"


@dataclass(frozen=True, slots=True)
class ExchangeError(Exception):
    code: ExchangeErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
