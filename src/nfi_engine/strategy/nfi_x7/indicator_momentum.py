from __future__ import annotations

from decimal import Decimal

from nfi_engine.strategy.nfi_x7.indicator_types import (
    ONE_HUNDRED,
    DecimalSeries,
    IndicatorSeries,
    OhlcvSeries,
    StochasticConfig,
    StochasticRsiConfig,
    StochasticSeries,
    require_equal_indicator_lengths,
    require_positive_period,
)
from nfi_engine.strategy.nfi_x7.indicator_windows import (
    rolling_max,
    rolling_mean_nullable,
    rolling_min,
)


def pct_change(values: DecimalSeries, *, period: int) -> IndicatorSeries:
    require_positive_period(period)
    output: list[Decimal | None] = []
    for index, value in enumerate(values):
        if index < period or values[index - period] == Decimal(0):
            output.append(None)
        else:
            previous = values[index - period]
            output.append((value - previous) / previous)
    return tuple(output)


def rate_of_change(values: DecimalSeries, *, period: int) -> IndicatorSeries:
    return tuple(
        value * ONE_HUNDRED if value is not None else None
        for value in pct_change(values, period=period)
    )


def relative_strength_index(values: DecimalSeries, *, period: int) -> IndicatorSeries:
    require_positive_period(period)
    output: list[Decimal | None] = [None] * len(values)
    if len(values) <= period:
        return tuple(output)
    gains: list[Decimal] = []
    losses: list[Decimal] = []
    for index in range(1, period + 1):
        gain, loss = _gain_loss(values[index] - values[index - 1])
        gains.append(gain)
        losses.append(loss)
    average_gain = sum(gains) / Decimal(period)
    average_loss = sum(losses) / Decimal(period)
    output[period] = _rsi_value(average_gain=average_gain, average_loss=average_loss)
    for index in range(period + 1, len(values)):
        gain, loss = _gain_loss(values[index] - values[index - 1])
        average_gain = ((average_gain * Decimal(period - 1)) + gain) / Decimal(period)
        average_loss = ((average_loss * Decimal(period - 1)) + loss) / Decimal(period)
        output[index] = _rsi_value(average_gain=average_gain, average_loss=average_loss)
    return tuple(output)


def stochastic_oscillator(series: OhlcvSeries, config: StochasticConfig) -> StochasticSeries:
    require_positive_period(config.k_period)
    require_positive_period(config.d_period)
    highest = rolling_max(series.high, window=config.k_period)
    lowest = rolling_min(series.low, window=config.k_period)
    percent_k = tuple(
        _bounded_percent(value=close, lowest=low, highest=high)
        for close, low, high in zip(series.close, lowest, highest, strict=True)
    )
    percent_d = rolling_mean_nullable(percent_k, window=config.d_period)
    return StochasticSeries(percent_k=percent_k, percent_d=percent_d)


def stochastic_rsi(values: DecimalSeries, config: StochasticRsiConfig) -> StochasticSeries:
    require_positive_period(config.rsi_period)
    require_positive_period(config.stoch_period)
    require_positive_period(config.smooth_k)
    require_positive_period(config.smooth_d)
    rsi_values = relative_strength_index(values, period=config.rsi_period)
    raw_k = _stochastic_nullable(rsi_values, window=config.stoch_period)
    percent_k = rolling_mean_nullable(raw_k, window=config.smooth_k)
    percent_d = rolling_mean_nullable(percent_k, window=config.smooth_d)
    return StochasticSeries(percent_k=percent_k, percent_d=percent_d)


def williams_r(series: OhlcvSeries, *, period: int) -> IndicatorSeries:
    require_positive_period(period)
    highest = rolling_max(series.high, window=period)
    lowest = rolling_min(series.low, window=period)
    return tuple(
        _williams_value(close=close, lowest=low, highest=high)
        for close, low, high in zip(series.close, lowest, highest, strict=True)
    )


def crossed_above(left: IndicatorSeries, right: IndicatorSeries) -> tuple[bool, ...]:
    require_equal_indicator_lengths(left, right)
    return tuple(_crossed_up(left=left, right=right, index=index) for index in range(len(left)))


def crossed_below(left: IndicatorSeries, right: IndicatorSeries) -> tuple[bool, ...]:
    require_equal_indicator_lengths(left, right)
    return tuple(_crossed_down(left=left, right=right, index=index) for index in range(len(left)))


def _gain_loss(delta: Decimal) -> tuple[Decimal, Decimal]:
    if delta > Decimal(0):
        return delta, Decimal(0)
    return Decimal(0), abs(delta)


def _rsi_value(*, average_gain: Decimal, average_loss: Decimal) -> Decimal:
    if average_gain == Decimal(0) and average_loss == Decimal(0):
        return Decimal(50)
    if average_loss == Decimal(0):
        return ONE_HUNDRED
    relative_strength = average_gain / average_loss
    return ONE_HUNDRED - (ONE_HUNDRED / (Decimal(1) + relative_strength))


def _bounded_percent(
    *,
    value: Decimal,
    lowest: Decimal | None,
    highest: Decimal | None,
) -> Decimal | None:
    if lowest is None or highest is None or highest == lowest:
        return None
    return ((value - lowest) / (highest - lowest)) * ONE_HUNDRED


def _stochastic_nullable(values: IndicatorSeries, *, window: int) -> IndicatorSeries:
    output: list[Decimal | None] = []
    for index, value in enumerate(values):
        if index + 1 < window or value is None:
            output.append(None)
            continue
        window_values = values[index - window + 1 : index + 1]
        if any(item is None for item in window_values):
            output.append(None)
            continue
        concrete_values = tuple(item for item in window_values if item is not None)
        output.append(
            _bounded_percent(
                value=value,
                lowest=min(concrete_values),
                highest=max(concrete_values),
            )
        )
    return tuple(output)


def _williams_value(
    *,
    close: Decimal,
    lowest: Decimal | None,
    highest: Decimal | None,
) -> Decimal | None:
    if lowest is None or highest is None or highest == lowest:
        return None
    return ((highest - close) / (highest - lowest)) * -ONE_HUNDRED


def _crossed_up(*, left: IndicatorSeries, right: IndicatorSeries, index: int) -> bool:
    if index == 0:
        return False
    previous_left = left[index - 1]
    previous_right = right[index - 1]
    current_left = left[index]
    current_right = right[index]
    if (
        previous_left is None
        or previous_right is None
        or current_left is None
        or current_right is None
    ):
        return False
    return previous_left <= previous_right and current_left > current_right


def _crossed_down(*, left: IndicatorSeries, right: IndicatorSeries, index: int) -> bool:
    if index == 0:
        return False
    previous_left = left[index - 1]
    previous_right = right[index - 1]
    current_left = left[index]
    current_right = right[index]
    if (
        previous_left is None
        or previous_right is None
        or current_left is None
        or current_right is None
    ):
        return False
    return previous_left >= previous_right and current_left < current_right
