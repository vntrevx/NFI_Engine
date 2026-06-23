from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from nfi_engine.backtest.frames import strategy_rows_for_batch
from nfi_engine.data import load_candle_batch
from nfi_engine.strategy import (
    SignalColumns,
    StrategyContractError,
    StrategyErrorCode,
    StrategyFeature,
    StrategyFeatureName,
    StrategyFrame,
    StrategyRow,
)

FIXTURE_ROOT = Path("tests/fixtures/candles")


def test_strategy_frame_reads_only_visible_cursor_rows() -> None:
    frame = _frame(visible_row_count=2)

    assert tuple(row.close for row in frame.visible_rows()) == (Decimal(10), Decimal(11))
    assert frame.last_visible_row().close == Decimal(11)
    assert frame.visible().rows == frame.rows[:2]
    assert frame.visible().visible_row_count is None


def test_strategy_frame_rejects_future_rows_when_cursor_hides_rows() -> None:
    with pytest.raises(StrategyContractError) as exc_info:
        _frame(visible_row_count=2).future_rows()

    assert exc_info.value.code is StrategyErrorCode.LOOKAHEAD_ACCESS


def test_strategy_frame_writes_signal_only_inside_visible_cursor() -> None:
    frame = _frame(visible_row_count=2)

    updated = frame.with_signal(index=-1, columns=SignalColumns(enter_long=True))

    assert updated.rows[0].enter_long is False
    assert updated.rows[1].enter_long is True
    assert updated.rows[2].enter_long is False
    with pytest.raises(StrategyContractError):
        frame.with_signal(index=2, columns=SignalColumns(enter_long=True))


def test_strategy_rows_preserve_candle_ohlcv_when_built_from_batch() -> None:
    batch = load_candle_batch(FIXTURE_ROOT / "btc_usdt_5m.jsonl")

    rows = strategy_rows_for_batch(batch=batch)

    assert rows[0].open == Decimal(100)
    assert rows[0].high == Decimal(105)
    assert rows[0].low == Decimal(99)
    assert rows[0].close == Decimal(102)
    assert rows[0].volume == Decimal("1.0")


def test_strategy_frame_updates_features_without_mutating_hidden_rows() -> None:
    frame = _frame(visible_row_count=2)
    feature_name = StrategyFeatureName("rsi_14")

    first_update = frame.with_feature(
        index=-1,
        feature=StrategyFeature(name=feature_name, value=Decimal("41.5")),
    )
    second_update = first_update.with_feature(
        index=-1,
        feature=StrategyFeature(name=feature_name, value=Decimal("42.5")),
    )

    assert frame.rows[1].features == ()
    assert first_update.rows[1].feature(feature_name) == Decimal("41.5")
    assert second_update.rows[1].feature(feature_name) == Decimal("42.5")
    assert len(second_update.rows[1].features) == 1
    assert second_update.rows[2].features == ()


def test_strategy_row_bulk_feature_update_matches_repeated_updates() -> None:
    row = StrategyRow(date="2026-01-01T00:00:00Z", close=Decimal(10))
    features = (
        StrategyFeature(name=StrategyFeatureName("ema_3"), value=Decimal("10.1")),
        StrategyFeature(name=StrategyFeatureName("rsi_3"), value=Decimal(42)),
        StrategyFeature(name=StrategyFeatureName("ema_3"), value=Decimal("10.2")),
    )
    repeated = row
    for feature in features:
        repeated = repeated.with_feature(feature)

    bulk = row.with_features(features)

    assert bulk.features == repeated.features
    assert bulk.feature(StrategyFeatureName("ema_3")) == Decimal("10.2")
    assert bulk.feature(StrategyFeatureName("rsi_3")) == Decimal(42)


def test_strategy_frame_rejects_missing_feature_and_future_feature_write() -> None:
    frame = _frame(visible_row_count=2)
    feature = StrategyFeature(
        name=StrategyFeatureName("ema_12"),
        value=Decimal("101.5"),
    )

    with pytest.raises(StrategyContractError) as missing_feature:
        frame.last_visible_row().feature(StrategyFeatureName("ema_12"))
    with pytest.raises(StrategyContractError) as future_write:
        frame.with_feature(index=2, feature=feature)

    assert missing_feature.value.code is StrategyErrorCode.STRATEGY_FEATURE_NOT_FOUND
    assert future_write.value.code is StrategyErrorCode.STRATEGY_CONTRACT_ERROR


def _frame(*, visible_row_count: int) -> StrategyFrame:
    return StrategyFrame(
        rows=(
            StrategyRow(date="2026-01-01T00:00:00Z", close=Decimal(10)),
            StrategyRow(date="2026-01-01T00:05:00Z", close=Decimal(11)),
            StrategyRow(date="2026-01-01T00:10:00Z", close=Decimal(12)),
        ),
        visible_row_count=visible_row_count,
    )
