from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class StrategyErrorCode(StrEnum):
    DATA_PROVIDER_FRAME_NOT_FOUND = "DATA_PROVIDER_FRAME_NOT_FOUND"
    DATA_PROVIDER_FRAME_STALE = "DATA_PROVIDER_FRAME_STALE"
    STRATEGY_FEATURE_NOT_FOUND = "STRATEGY_FEATURE_NOT_FOUND"
    LOOKAHEAD_ACCESS = "LOOKAHEAD_ACCESS"
    STRATEGY_CONTRACT_ERROR = "STRATEGY_CONTRACT_ERROR"
    STRATEGY_LOAD_ERROR = "STRATEGY_LOAD_ERROR"


@dataclass(frozen=True, slots=True)
class StrategyContractError(Exception):
    code: StrategyErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"
