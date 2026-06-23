from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum, unique
from typing import Final, override

type DecimalSeries = tuple[Decimal, ...]
type IndicatorSeries = tuple[Decimal | None, ...]

ONE_HUNDRED: Final = Decimal(100)
TWO: Final = Decimal(2)


@unique
class X7IndicatorErrorCode(StrEnum):
    INVALID_PERIOD = "INVALID_PERIOD"
    SERIES_LENGTH_MISMATCH = "SERIES_LENGTH_MISMATCH"


@dataclass(frozen=True, slots=True)
class X7IndicatorError(Exception):
    code: X7IndicatorErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


@dataclass(frozen=True, slots=True)
class OhlcvSeries:
    high: DecimalSeries
    low: DecimalSeries
    close: DecimalSeries
    volume: DecimalSeries

    def __post_init__(self) -> None:
        lengths = {len(self.high), len(self.low), len(self.close), len(self.volume)}
        if len(lengths) != 1:
            raise X7IndicatorError(
                code=X7IndicatorErrorCode.SERIES_LENGTH_MISMATCH,
                message="OHLCV series lengths must match",
            )


@dataclass(frozen=True, slots=True)
class StochasticConfig:
    k_period: int
    d_period: int


@dataclass(frozen=True, slots=True)
class StochasticRsiConfig:
    rsi_period: int
    stoch_period: int
    smooth_k: int
    smooth_d: int


@dataclass(frozen=True, slots=True)
class StochasticSeries:
    percent_k: IndicatorSeries
    percent_d: IndicatorSeries


def require_positive_period(period: int) -> None:
    if period <= 0:
        raise X7IndicatorError(
            code=X7IndicatorErrorCode.INVALID_PERIOD,
            message="indicator period must be positive",
        )


def require_equal_indicator_lengths(left: IndicatorSeries, right: IndicatorSeries) -> None:
    if len(left) != len(right):
        raise X7IndicatorError(
            code=X7IndicatorErrorCode.SERIES_LENGTH_MISMATCH,
            message="indicator series lengths must match",
        )
