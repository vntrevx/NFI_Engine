from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from nfi_engine.strategy import (
    StrategyContractError,
    StrategyErrorCode,
    StrategyFeature,
    StrategyFeatureName,
    StrategyFrame,
    StrategyRow,
)
from nfi_engine.strategy.nfi_x7.feature_graph_models import (
    X7_FEATURE_GRAPH_FEATURE_BUDGET,
    X7FeatureGraphCoverage,
    X7FeatureGraphResult,
    X7FrameCursorSignature,
)
from nfi_engine.strategy.nfi_x7.indicators import (
    IndicatorSeries,
    OhlcvSeries,
    StochasticConfig,
    average_true_range,
    chaikin_money_flow,
    exponential_moving_average,
    range_percent,
    rate_of_change,
    relative_strength_index,
    stochastic_oscillator,
    williams_r,
)

ZERO: Decimal = Decimal(0)


@dataclass(frozen=True, slots=True)
class X7NamedFeatureSeries:
    name: StrategyFeatureName
    values: IndicatorSeries


@dataclass(frozen=True, slots=True)
class X7InformativeFrames:
    timeframe: str
    base_frame: StrategyFrame
    btc_frame: StrategyFrame


def build_feature_graph_result(
    *,
    base_frame: StrategyFrame,
    informative_frames: tuple[X7InformativeFrames, ...],
) -> X7FeatureGraphResult:
    base_rows = base_frame.visible_rows()
    base_features = _base_feature_series(base_rows)
    informative_features = _informative_feature_series(
        base_rows=base_rows,
        informative_frames=informative_frames,
    )
    feature_series = (*base_features, *informative_features)
    _require_feature_budget(feature_series)
    return X7FeatureGraphResult(
        frame=StrategyFrame(
            rows=_rows_with_features(rows=base_rows, feature_series=feature_series)
        ),
        coverage=X7FeatureGraphCoverage(
            base_feature_count=len(base_features),
            informative_feature_count=len(informative_features),
            informative_timeframes=tuple(frames.timeframe for frames in informative_frames),
            feature_names=tuple(feature.name for feature in feature_series),
        ),
    )


def cursor_signature(frame: StrategyFrame) -> X7FrameCursorSignature:
    rows = frame.visible_rows()
    return X7FrameCursorSignature(
        row_count=len(rows),
        first_date=rows[0].date if len(rows) > 0 else None,
        last_date=rows[-1].date if len(rows) > 0 else None,
        close_sum=sum((row.close for row in rows), start=ZERO),
        high_sum=sum((row.high for row in rows), start=ZERO),
        low_sum=sum((row.low for row in rows), start=ZERO),
        volume_sum=sum((row.volume for row in rows), start=ZERO),
    )


def _base_feature_series(rows: tuple[StrategyRow, ...]) -> tuple[X7NamedFeatureSeries, ...]:
    series = _ohlcv_series(rows)
    stochastic = stochastic_oscillator(series, StochasticConfig(k_period=3, d_period=2))
    return (
        _named("x7_base_ema_3", exponential_moving_average(series.close, period=3)),
        _named("x7_base_rsi_3", relative_strength_index(series.close, period=3)),
        _named("x7_base_roc_1", rate_of_change(series.close, period=1)),
        _named("x7_base_roc_2", rate_of_change(series.close, period=2)),
        _named("x7_base_atr_3", average_true_range(series, period=3)),
        _named("x7_base_range_pct", range_percent(series)),
        _named("x7_base_stoch_k_3", stochastic.percent_k),
        _named("x7_base_cmf_3", chaikin_money_flow(series, period=3)),
        _named("x7_base_williams_r_3", williams_r(series, period=3)),
    )


def _informative_feature_series(
    *,
    base_rows: tuple[StrategyRow, ...],
    informative_frames: tuple[X7InformativeFrames, ...],
) -> tuple[X7NamedFeatureSeries, ...]:
    output: tuple[X7NamedFeatureSeries, ...] = ()
    for frames in informative_frames:
        output += _aligned_feature_series(
            source="base",
            timeframe=frames.timeframe,
            base_rows=base_rows,
            informative_rows=frames.base_frame.visible_rows(),
        )
        output += _aligned_feature_series(
            source="btc",
            timeframe=frames.timeframe,
            base_rows=base_rows,
            informative_rows=frames.btc_frame.visible_rows(),
        )
    return output


def _aligned_feature_series(
    *,
    source: str,
    timeframe: str,
    base_rows: tuple[StrategyRow, ...],
    informative_rows: tuple[StrategyRow, ...],
) -> tuple[X7NamedFeatureSeries, ...]:
    series = _ohlcv_series(informative_rows)
    prefix = f"x7_{source}_{timeframe}"
    return tuple(
        X7NamedFeatureSeries(
            name=feature.name,
            values=_align_to_base_rows(
                base_rows=base_rows,
                informative_rows=informative_rows,
                values=feature.values,
            ),
        )
        for feature in (
            _named(f"{prefix}_range_pct", range_percent(series)),
            _named(f"{prefix}_roc_1", rate_of_change(series.close, period=1)),
            _named(f"{prefix}_ema_2", exponential_moving_average(series.close, period=2)),
        )
    )


def _align_to_base_rows(
    *,
    base_rows: tuple[StrategyRow, ...],
    informative_rows: tuple[StrategyRow, ...],
    values: IndicatorSeries,
) -> IndicatorSeries:
    aligned: list[Decimal | None] = []
    cursor = -1
    for row in base_rows:
        while _has_next_asof_row(
            cursor=cursor,
            informative_rows=informative_rows,
            row_date=row.date,
        ):
            cursor += 1
        aligned.append(None if cursor < 0 else values[cursor])
    return tuple(aligned)


def _has_next_asof_row(
    *,
    cursor: int,
    informative_rows: tuple[StrategyRow, ...],
    row_date: str,
) -> bool:
    next_index = cursor + 1
    return next_index < len(informative_rows) and informative_rows[next_index].date <= row_date


def _rows_with_features(
    *,
    rows: tuple[StrategyRow, ...],
    feature_series: tuple[X7NamedFeatureSeries, ...],
) -> tuple[StrategyRow, ...]:
    updated_rows: list[StrategyRow] = []
    for row_index, row in enumerate(rows):
        row_features: list[StrategyFeature] = []
        for feature in feature_series:
            value = feature.values[row_index]
            if value is not None:
                row_features.append(StrategyFeature(name=feature.name, value=value))
        updated_rows.append(row.with_features(tuple(row_features)))
    return tuple(updated_rows)


def _ohlcv_series(rows: tuple[StrategyRow, ...]) -> OhlcvSeries:
    return OhlcvSeries(
        high=tuple(row.high for row in rows),
        low=tuple(row.low for row in rows),
        close=tuple(row.close for row in rows),
        volume=tuple(row.volume for row in rows),
    )


def _named(name: str, values: IndicatorSeries) -> X7NamedFeatureSeries:
    return X7NamedFeatureSeries(name=StrategyFeatureName(name), values=values)


def _require_feature_budget(feature_series: tuple[X7NamedFeatureSeries, ...]) -> None:
    if len(feature_series) <= X7_FEATURE_GRAPH_FEATURE_BUDGET:
        return
    raise StrategyContractError(
        code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
        message="X7 feature graph exceeded the native feature budget",
    )
