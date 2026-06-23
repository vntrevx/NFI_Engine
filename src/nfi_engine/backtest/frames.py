from __future__ import annotations

from decimal import Decimal

from nfi_engine.data import CandleBatch
from nfi_engine.domain import Candle
from nfi_engine.strategy import StrategyFrame, StrategyOhlcv, StrategyRow


def strategy_frame_for_cursor(*, batch: CandleBatch, visible_count: int) -> StrategyFrame:
    return strategy_frame_from_rows(
        rows=strategy_rows_for_batch(batch=batch),
        visible_count=visible_count,
    )


def strategy_rows_for_batch(*, batch: CandleBatch) -> tuple[StrategyRow, ...]:
    return tuple(_strategy_row(candle) for candle in batch.candles)


def strategy_frame_from_rows(
    *,
    rows: tuple[StrategyRow, ...],
    visible_count: int,
) -> StrategyFrame:
    return StrategyFrame(
        rows=rows,
        visible_row_count=visible_count,
    )


def candle_close(candle: Candle) -> Decimal:
    return candle.close


def candle_high(candle: Candle) -> Decimal:
    return candle.high


def candle_low(candle: Candle) -> Decimal:
    return candle.low


def _strategy_row(candle: Candle) -> StrategyRow:
    return StrategyRow(
        date=candle.opened_at.isoformat(),
        close=candle.close,
        ohlcv=StrategyOhlcv(
            open=candle.open,
            high=candle.high,
            low=candle.low,
            close=candle.close,
            volume=candle.volume,
        ),
    )
