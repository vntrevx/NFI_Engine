from __future__ import annotations

from decimal import Decimal

from nfi_engine.strategy.nfi_x7.indicator_types import (
    ONE_HUNDRED,
    IndicatorSeries,
    OhlcvSeries,
    require_positive_period,
)
from nfi_engine.strategy.nfi_x7.indicator_windows import rolling_sum


def chaikin_money_flow(series: OhlcvSeries, *, period: int) -> IndicatorSeries:
    require_positive_period(period)
    money_flow_volume = tuple(
        _money_flow_multiplier(high=high, low=low, close=close) * volume
        for high, low, close, volume in zip(
            series.high,
            series.low,
            series.close,
            series.volume,
            strict=True,
        )
    )
    flow_sum = rolling_sum(money_flow_volume, window=period)
    volume_sum = rolling_sum(series.volume, window=period)
    return tuple(
        flow / volume if flow is not None and volume not in (None, Decimal(0)) else None
        for flow, volume in zip(flow_sum, volume_sum, strict=True)
    )


def true_range(series: OhlcvSeries) -> tuple[Decimal, ...]:
    output: list[Decimal] = []
    for index, high in enumerate(series.high):
        low = series.low[index]
        if index == 0:
            output.append(high - low)
        else:
            previous_close = series.close[index - 1]
            output.append(max(high - low, abs(high - previous_close), abs(low - previous_close)))
    return tuple(output)


def average_true_range(series: OhlcvSeries, *, period: int) -> IndicatorSeries:
    require_positive_period(period)
    ranges = true_range(series)
    output: list[Decimal | None] = [None] * len(ranges)
    if len(ranges) < period:
        return tuple(output)
    previous = sum(ranges[:period]) / Decimal(period)
    output[period - 1] = previous
    for index in range(period, len(ranges)):
        previous = ((previous * Decimal(period - 1)) + ranges[index]) / Decimal(period)
        output[index] = previous
    return tuple(output)


def range_percent(series: OhlcvSeries) -> IndicatorSeries:
    return tuple(
        ((high - low) / close) * ONE_HUNDRED if close != Decimal(0) else None
        for high, low, close in zip(series.high, series.low, series.close, strict=True)
    )


def _money_flow_multiplier(*, high: Decimal, low: Decimal, close: Decimal) -> Decimal:
    if high == low:
        return Decimal(0)
    return ((close - low) - (high - close)) / (high - low)
