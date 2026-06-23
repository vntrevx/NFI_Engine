from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from nfi_engine.backtest.frames import strategy_frame_for_cursor
from nfi_engine.data import load_candle_batch
from nfi_engine.strategy import (
    DataProviderFacade,
    PairFrame,
    StrategyContractError,
    StrategyErrorCode,
    StrategyFeatureName,
    StrategyFrame,
)
from nfi_engine.strategy.nfi_x7 import (
    X7FeatureGraph,
    X7FeatureGraphContext,
    X7FeatureGraphRequest,
)

FIXTURE_ROOT = Path("tests/fixtures/candles")
FEATURE_BUDGET = 64


def test_feature_graph_adds_deterministic_bounded_features_from_base_and_informatives() -> None:
    # Given
    base_frame, provider = _feature_graph_inputs(visible_count=6)
    graph = X7FeatureGraph()
    context = X7FeatureGraphContext(
        base_frame=base_frame,
        provider=provider,
        request=X7FeatureGraphRequest(
            pair=load_candle_batch(FIXTURE_ROOT / "btc_usdt_5m.jsonl").pair,
            base_timeframe="5m",
            informative_timeframes=("15m", "1h"),
        ),
    )

    # When
    first = graph.build(context)
    second = graph.build(context)

    # Then
    assert first == second
    assert first.cache_hit is False
    assert second.cache_hit is True
    assert graph.cache_stats.hit_count == 1
    assert graph.cache_stats.miss_count == 1
    assert first.coverage.base_feature_count >= 8
    assert first.coverage.informative_feature_count >= 6
    assert first.coverage.total_feature_count <= FEATURE_BUDGET
    assert first.coverage.informative_timeframes == ("15m", "1h")
    assert first.frame.last_visible_row().feature(StrategyFeatureName("x7_base_rsi_3")) == Decimal(
        "65.38461538461538461538461537",
    )
    assert first.frame.last_visible_row().feature(
        StrategyFeatureName("x7_base_15m_range_pct"),
    ) == Decimal("6.481481481481481481481481481")


def test_feature_graph_uses_only_visible_rows_and_never_enriches_hidden_future_rows() -> None:
    # Given
    base_frame, provider = _feature_graph_inputs(visible_count=4)
    graph = X7FeatureGraph()
    context = X7FeatureGraphContext(
        base_frame=base_frame,
        provider=provider,
        request=X7FeatureGraphRequest(
            pair=load_candle_batch(FIXTURE_ROOT / "btc_usdt_5m.jsonl").pair,
            base_timeframe="5m",
            informative_timeframes=("15m",),
        ),
    )

    # When
    result = graph.build(context)

    # Then
    assert len(result.frame.rows) == 4
    assert result.frame.rows[-1].date == "2026-01-01T00:15:00+00:00"
    assert result.frame.future_rows() == ()


def test_feature_graph_rejects_missing_informative_frame_without_synthesis() -> None:
    # Given
    base_frame, provider = _feature_graph_inputs(visible_count=6)
    graph = X7FeatureGraph()
    context = X7FeatureGraphContext(
        base_frame=base_frame,
        provider=provider,
        request=X7FeatureGraphRequest(
            pair=load_candle_batch(FIXTURE_ROOT / "btc_usdt_5m.jsonl").pair,
            base_timeframe="5m",
            informative_timeframes=("4h",),
        ),
    )

    # When
    with pytest.raises(StrategyContractError) as exc_info:
        graph.build(context)

    # Then
    assert exc_info.value.code is StrategyErrorCode.DATA_PROVIDER_FRAME_NOT_FOUND


def _feature_graph_inputs(*, visible_count: int) -> tuple[StrategyFrame, DataProviderFacade]:
    base = load_candle_batch(FIXTURE_ROOT / "btc_usdt_5m.jsonl")
    informative_15m = load_candle_batch(FIXTURE_ROOT / "btc_usdt_15m.jsonl")
    informative_1h = load_candle_batch(FIXTURE_ROOT / "btc_usdt_1h.jsonl")
    base_frame = strategy_frame_for_cursor(batch=base, visible_count=visible_count)
    provider = DataProviderFacade(
        frames=(
            PairFrame(
                pair=base.pair,
                timeframe=base.timeframe,
                frame=base_frame,
            ),
            PairFrame(
                pair=informative_15m.pair,
                timeframe=informative_15m.timeframe,
                frame=strategy_frame_for_cursor(
                    batch=informative_15m,
                    visible_count=len(informative_15m.candles),
                ),
            ),
            PairFrame(
                pair=informative_1h.pair,
                timeframe=informative_1h.timeframe,
                frame=strategy_frame_for_cursor(
                    batch=informative_1h,
                    visible_count=len(informative_1h.candles),
                ),
            ),
        ),
    )
    return base_frame, provider
