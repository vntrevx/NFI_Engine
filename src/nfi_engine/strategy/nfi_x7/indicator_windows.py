from __future__ import annotations

from collections import deque
from decimal import Decimal

from nfi_engine.strategy.nfi_x7.indicator_types import (
    TWO,
    DecimalSeries,
    IndicatorSeries,
    require_positive_period,
)


def rolling_sum(values: DecimalSeries, *, window: int) -> IndicatorSeries:
    require_positive_period(window)
    output: list[Decimal | None] = []
    total = Decimal(0)
    for index, value in enumerate(values):
        total += value
        if index >= window:
            total -= values[index - window]
        output.append(total if index + 1 >= window else None)
    return tuple(output)


def rolling_mean(values: DecimalSeries, *, window: int) -> IndicatorSeries:
    require_positive_period(window)
    divisor = Decimal(window)
    return tuple(
        value / divisor if value is not None else None
        for value in rolling_sum(values, window=window)
    )


def rolling_min(values: DecimalSeries, *, window: int) -> IndicatorSeries:
    require_positive_period(window)
    output: list[Decimal | None] = []
    indexes: deque[int] = deque()
    for index, value in enumerate(values):
        while len(indexes) > 0 and indexes[0] <= index - window:
            indexes.popleft()
        while len(indexes) > 0 and values[indexes[-1]] >= value:
            indexes.pop()
        indexes.append(index)
        output.append(values[indexes[0]] if index + 1 >= window else None)
    return tuple(output)


def rolling_max(values: DecimalSeries, *, window: int) -> IndicatorSeries:
    require_positive_period(window)
    output: list[Decimal | None] = []
    indexes: deque[int] = deque()
    for index, value in enumerate(values):
        while len(indexes) > 0 and indexes[0] <= index - window:
            indexes.popleft()
        while len(indexes) > 0 and values[indexes[-1]] <= value:
            indexes.pop()
        indexes.append(index)
        output.append(values[indexes[0]] if index + 1 >= window else None)
    return tuple(output)


def simple_moving_average(values: DecimalSeries, *, window: int) -> IndicatorSeries:
    return rolling_mean(values, window=window)


def exponential_moving_average(values: DecimalSeries, *, period: int) -> IndicatorSeries:
    require_positive_period(period)
    output: list[Decimal | None] = [None] * len(values)
    if len(values) < period:
        return tuple(output)
    multiplier = TWO / Decimal(period + 1)
    previous = sum(values[:period]) / Decimal(period)
    output[period - 1] = previous
    for index in range(period, len(values)):
        previous = (values[index] - previous) * multiplier + previous
        output[index] = previous
    return tuple(output)


def rolling_mean_nullable(values: IndicatorSeries, *, window: int) -> IndicatorSeries:
    require_positive_period(window)
    output: list[Decimal | None] = []
    for index in range(len(values)):
        if index + 1 < window:
            output.append(None)
            continue
        window_values = values[index - window + 1 : index + 1]
        if any(value is None for value in window_values):
            output.append(None)
        else:
            output.append(
                sum(value for value in window_values if value is not None) / Decimal(window)
            )
    return tuple(output)
