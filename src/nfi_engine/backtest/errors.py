from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class BacktestErrorCode(StrEnum):
    BACKTEST_NO_CANDLES = "BACKTEST_NO_CANDLES"
    BACKTEST_TIMERANGE_INVALID = "BACKTEST_TIMERANGE_INVALID"
    LIQUIDATION_BUFFER_VIOLATION = "LIQUIDATION_BUFFER_VIOLATION"
    SHORT_SIGNAL_NOT_ALLOWED = "SHORT_SIGNAL_NOT_ALLOWED"


@dataclass(frozen=True, slots=True)
class BacktestError(Exception):
    code: BacktestErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
