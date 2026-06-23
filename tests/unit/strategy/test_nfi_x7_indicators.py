from __future__ import annotations

from decimal import Decimal

import pytest

from nfi_engine.strategy.nfi_x7.indicators import (
    OhlcvSeries,
    StochasticConfig,
    StochasticRsiConfig,
    X7IndicatorError,
    X7IndicatorErrorCode,
    average_true_range,
    chaikin_money_flow,
    crossed_above,
    crossed_below,
    exponential_moving_average,
    pct_change,
    range_percent,
    rate_of_change,
    relative_strength_index,
    rolling_max,
    rolling_mean,
    rolling_min,
    rolling_sum,
    simple_moving_average,
    stochastic_oscillator,
    stochastic_rsi,
    true_range,
    williams_r,
)


def test_rolling_and_moving_averages_are_bounded_and_deterministic() -> None:
    # Given
    values = _series("1", "2", "3", "4", "5")

    # When
    sums = rolling_sum(values, window=3)
    means = rolling_mean(values, window=3)
    lows = rolling_min(values, window=3)
    highs = rolling_max(values, window=3)
    simple = simple_moving_average(values, window=3)
    exponential = exponential_moving_average(values, period=3)

    # Then
    assert sums == (None, None, Decimal(6), Decimal(9), Decimal(12))
    assert means == (None, None, Decimal(2), Decimal(3), Decimal(4))
    assert lows == (None, None, Decimal(1), Decimal(2), Decimal(3))
    assert highs == (None, None, Decimal(3), Decimal(4), Decimal(5))
    assert simple == means
    assert exponential == (None, None, Decimal(2), Decimal(3), Decimal(4))


def test_momentum_oscillators_handle_warmup_and_zero_denominators() -> None:
    # Given
    rising = _series("1", "2", "3", "4", "5")
    flat = _series("10", "10", "10", "10")
    with_zero = _series("0", "2", "4")

    # When
    fractional_change = pct_change(rising, period=2)
    percent_change = rate_of_change(rising, period=2)
    rising_rsi = relative_strength_index(rising, period=3)
    flat_rsi = relative_strength_index(flat, period=3)
    zero_change = pct_change(with_zero, period=1)

    # Then
    assert fractional_change == (
        None,
        None,
        Decimal(2),
        Decimal(1),
        Decimal("0.6666666666666666666666666667"),
    )
    assert percent_change == (
        None,
        None,
        Decimal(200),
        Decimal(100),
        Decimal("66.66666666666666666666666667"),
    )
    assert rising_rsi == (None, None, None, Decimal(100), Decimal(100))
    assert flat_rsi == (None, None, None, Decimal(50))
    assert zero_change == (None, None, Decimal(1))


def test_stochastic_indicators_use_only_complete_windows() -> None:
    # Given
    ohlcv = OhlcvSeries(
        high=_series("10", "11", "12", "13", "14"),
        low=_series("5", "5", "6", "7", "8"),
        close=_series("7", "10", "11", "12", "13"),
        volume=_series("1", "1", "1", "1", "1"),
    )
    closes = _series("1", "2", "3", "2", "1", "2", "3", "4")

    # When
    stochastic = stochastic_oscillator(ohlcv, StochasticConfig(k_period=3, d_period=2))
    stoch_rsi = stochastic_rsi(
        closes,
        StochasticRsiConfig(rsi_period=2, stoch_period=3, smooth_k=2, smooth_d=2),
    )

    # Then
    assert stochastic.percent_k[:3] == (None, None, Decimal("85.71428571428571428571428571"))
    assert _rounded(stochastic.percent_d[3]) == Decimal("86.6071")
    assert stoch_rsi.percent_k[:5] == (None, None, None, None, None)
    assert _rounded(stoch_rsi.percent_k[-1]) == Decimal("100.0000")
    assert _rounded(stoch_rsi.percent_d[-1]) == Decimal("100.0000")


def test_volume_volatility_range_and_cross_helpers_are_safe() -> None:
    # Given
    ohlcv = OhlcvSeries(
        high=_series("10", "12", "11", "13"),
        low=_series("8", "9", "9", "10"),
        close=_series("9", "11", "10", "12"),
        volume=_series("100", "150", "120", "130"),
    )
    left = (None, Decimal(1), Decimal(2), Decimal(1), Decimal(3))
    right = (Decimal(1), Decimal(1), Decimal(1), Decimal(1), Decimal(2))

    # When
    wr = williams_r(ohlcv, period=2)
    cmf = chaikin_money_flow(ohlcv, period=2)
    ranges = true_range(ohlcv)
    atr = average_true_range(ohlcv, period=2)
    range_pct = range_percent(ohlcv)
    above = crossed_above(left, right)
    below = crossed_below((None, Decimal(2), Decimal(0)), (Decimal(1), Decimal(1), Decimal(1)))

    # Then
    assert _rounded(wr[2]) == Decimal("-66.6667")
    assert wr[0] is None
    assert wr[1] == Decimal(-25)
    assert wr[3] == Decimal(-25)
    assert cmf[0] is None
    assert cmf[1] == Decimal("0.2")
    assert _rounded(cmf[2]) == Decimal("0.1852")
    assert _rounded(cmf[3]) == Decimal("0.1733")
    assert ranges == (Decimal(2), Decimal(3), Decimal(2), Decimal(3))
    assert atr == (None, Decimal("2.5"), Decimal("2.25"), Decimal("2.625"))
    assert _rounded(range_pct[0]) == Decimal("22.2222")
    assert above == (False, False, True, False, True)
    assert below == (False, False, True)


def test_indicator_primitives_reject_invalid_period_and_length_mismatch() -> None:
    # Given
    values = _series("1", "2", "3")

    # When
    with pytest.raises(X7IndicatorError) as invalid_period:
        rolling_mean(values, window=0)
    with pytest.raises(X7IndicatorError) as length_mismatch:
        OhlcvSeries(
            high=_series("1", "2"),
            low=_series("1"),
            close=_series("1", "2"),
            volume=_series("1", "2"),
        )

    # Then
    assert invalid_period.value.code is X7IndicatorErrorCode.INVALID_PERIOD
    assert length_mismatch.value.code is X7IndicatorErrorCode.SERIES_LENGTH_MISMATCH


def _series(*raw_values: str) -> tuple[Decimal, ...]:
    return tuple(Decimal(raw_value) for raw_value in raw_values)


def _rounded(value: Decimal | None) -> Decimal:
    assert value is not None
    return value.quantize(Decimal("0.0001"))
