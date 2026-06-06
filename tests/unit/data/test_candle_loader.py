from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from nfi_engine.data import (
    DataErrorCode,
    DataLoadError,
    align_candle_batch,
    join_informative_candles,
    load_candle_batch,
)

FIXTURE_DIR = Path("tests/fixtures/candles")


def test_load_candle_batch_parses_schema_when_fixture_valid() -> None:
    # Given
    fixture_path = FIXTURE_DIR / "btc_usdt_5m.jsonl"

    # When
    batch = load_candle_batch(fixture_path)

    # Then
    assert batch.pair.normalized == "BTC/USDT"
    assert batch.timeframe == "5m"
    assert len(batch.candles) == 6
    assert batch.candles[0].close == Decimal(102)


def test_load_candle_batch_parses_futures_settle_pair_when_fixture_valid() -> None:
    # Given
    fixture_path = FIXTURE_DIR / "btc_usdt_usdt_futures_5m.jsonl"

    # When
    batch = load_candle_batch(fixture_path)

    # Then
    assert batch.pair.normalized == "BTC/USDT:USDT"
    assert batch.timeframe == "5m"


def test_load_candle_batch_rejects_duplicate_timestamps() -> None:
    # Given
    fixture_path = FIXTURE_DIR / "duplicate_timestamp.jsonl"

    # When
    with pytest.raises(DataLoadError) as exc_info:
        load_candle_batch(fixture_path)

    # Then
    assert exc_info.value.code is DataErrorCode.CANDLE_DUPLICATE_TIMESTAMP


def test_load_candle_batch_rejects_missing_required_column() -> None:
    # Given
    fixture_path = FIXTURE_DIR / "missing_column.jsonl"

    # When
    with pytest.raises(DataLoadError) as exc_info:
        load_candle_batch(fixture_path)

    # Then
    assert exc_info.value.code is DataErrorCode.CANDLE_SCHEMA_MISSING_COLUMN


def test_load_candle_batch_rejects_timeframe_gap() -> None:
    # Given
    fixture_path = FIXTURE_DIR / "gap_5m.jsonl"

    # When
    with pytest.raises(DataLoadError) as exc_info:
        load_candle_batch(fixture_path)

    # Then
    assert exc_info.value.code is DataErrorCode.CANDLE_TIMEFRAME_MISMATCH


def test_align_candle_batch_aggregates_5m_to_15m() -> None:
    # Given
    batch = load_candle_batch(FIXTURE_DIR / "btc_usdt_5m.jsonl")

    # When
    aligned = align_candle_batch(batch, target_timeframe="15m")

    # Then
    assert aligned.timeframe == "15m"
    assert len(aligned.candles) == 2
    assert aligned.candles[0].open == Decimal(100)
    assert aligned.candles[0].high == Decimal(109)
    assert aligned.candles[0].low == Decimal(99)
    assert aligned.candles[0].close == Decimal(107)
    assert aligned.candles[0].volume == Decimal("4.5")


def test_join_informative_candles_uses_backward_asof_without_lookahead() -> None:
    # Given
    base = load_candle_batch(FIXTURE_DIR / "btc_usdt_5m.jsonl")
    informative = load_candle_batch(FIXTURE_DIR / "btc_usdt_15m.jsonl")

    # When
    joined = join_informative_candles(base=base, informative=informative)

    # Then
    assert joined.rows[2].base_opened_at.isoformat() == "2026-01-01T00:10:00+00:00"
    assert joined.rows[2].informative_opened_at.isoformat() == "2026-01-01T00:00:00+00:00"
    assert joined.rows[2].informative_close == Decimal(107)
    assert joined.rows[3].base_opened_at.isoformat() == "2026-01-01T00:15:00+00:00"
    assert joined.rows[3].informative_opened_at.isoformat() == "2026-01-01T00:15:00+00:00"
    assert joined.rows[3].informative_close == Decimal(108)
