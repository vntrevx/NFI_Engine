from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import override


@unique
class DataErrorCode(StrEnum):
    CANDLE_DECIMAL_INVALID = "CANDLE_DECIMAL_INVALID"
    CANDLE_DUPLICATE_TIMESTAMP = "CANDLE_DUPLICATE_TIMESTAMP"
    CANDLE_EMPTY = "CANDLE_EMPTY"
    CANDLE_FILE_NOT_FOUND = "CANDLE_FILE_NOT_FOUND"
    CANDLE_INFORMATIVE_GAP = "CANDLE_INFORMATIVE_GAP"
    CANDLE_PAIR_MISMATCH = "CANDLE_PAIR_MISMATCH"
    CANDLE_READ_FAILED = "CANDLE_READ_FAILED"
    CANDLE_SCHEMA_MISSING_COLUMN = "CANDLE_SCHEMA_MISSING_COLUMN"
    CANDLE_TIMEFRAME_MISMATCH = "CANDLE_TIMEFRAME_MISMATCH"
    CANDLE_TIMESTAMP_INVALID = "CANDLE_TIMESTAMP_INVALID"


@dataclass(frozen=True, slots=True)
class DataLoadError(Exception):
    code: DataErrorCode
    message: str
    path: Path | None = None

    @override
    def __str__(self) -> str:
        if self.path is None:
            return f"{self.code.value}: {self.message}"
        return f"{self.code.value}: {self.message} path={self.path}"
