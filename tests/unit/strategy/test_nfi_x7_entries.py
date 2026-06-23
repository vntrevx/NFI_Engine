from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from nfi_engine.backtest.frames import strategy_frame_for_cursor
from nfi_engine.data import load_candle_batch
from nfi_engine.domain import PositionSide, SignalType, TradingMode, TradingPair
from nfi_engine.strategy import (
    FreqtradeStrategyAdapter,
    RunMode,
    StrategyFrame,
    StrategyMetadata,
    StrategyRow,
)
from nfi_engine.strategy.nfi_x7 import X7NativeStrategy

FIXTURE_ROOT = Path("tests/fixtures/candles")
ENTRY_TAG_LONG = "x7-long-momentum-balanced"
ENTRY_TAG_SHORT = "x7-short-momentum-fade"


def test_x7_entry_decision_marks_long_when_feature_graph_shows_bounded_up_move() -> None:
    # Given
    strategy = X7NativeStrategy()
    adapter = FreqtradeStrategyAdapter.from_strategy(strategy)
    batch = load_candle_batch(FIXTURE_ROOT / "btc_usdt_usdt_futures_5m.jsonl")
    frame = strategy_frame_for_cursor(batch=batch, visible_count=2)

    # When
    signals = adapter.analyze(frame, _metadata(pair=batch.pair), incremental=True)

    # Then
    assert tuple((signal.side, signal.signal_type, signal.tag) for signal in signals) == (
        (PositionSide.LONG, SignalType.ENTER, ENTRY_TAG_LONG),
    )


def test_x7_entry_decision_marks_short_when_feature_graph_shows_bounded_down_move() -> None:
    # Given
    strategy = X7NativeStrategy()
    adapter = FreqtradeStrategyAdapter.from_strategy(strategy)
    pair = TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
    frame = StrategyFrame(
        rows=(
            StrategyRow(date="2026-01-01T00:00:00+00:00", close=Decimal(105)),
            StrategyRow(date="2026-01-01T00:05:00+00:00", close=Decimal(100)),
        ),
    )

    # When
    signals = adapter.analyze(frame, _metadata(pair=pair), incremental=True)

    # Then
    assert tuple((signal.side, signal.signal_type, signal.tag) for signal in signals) == (
        (PositionSide.SHORT, SignalType.ENTER, ENTRY_TAG_SHORT),
    )


def test_x7_entry_decision_keeps_warmup_rows_signal_free() -> None:
    # Given
    strategy = X7NativeStrategy()
    adapter = FreqtradeStrategyAdapter.from_strategy(strategy)
    batch = load_candle_batch(FIXTURE_ROOT / "btc_usdt_usdt_futures_5m.jsonl")
    frame = strategy_frame_for_cursor(batch=batch, visible_count=1)

    # When
    signals = adapter.analyze(frame, _metadata(pair=batch.pair), incremental=True)

    # Then
    assert signals == ()


def _metadata(*, pair: TradingPair) -> StrategyMetadata:
    return StrategyMetadata(pair=pair, timeframe="5m", runmode=RunMode.BACKTEST)
