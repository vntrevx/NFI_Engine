from __future__ import annotations

from decimal import Decimal

from nfi_engine.data import CandleBatch
from nfi_engine.domain import Candle
from nfi_engine.strategy import StrategyFrame, StrategyRow


def strategy_frame_for_cursor(*, batch: CandleBatch, visible_count: int) -> StrategyFrame:
    return StrategyFrame(
        rows=tuple(_strategy_row(candle) for candle in batch.candles),
        visible_row_count=visible_count,
    )


def candle_close(candle: Candle) -> Decimal:
    return candle.close


def candle_high(candle: Candle) -> Decimal:
    return candle.high


def candle_low(candle: Candle) -> Decimal:
    return candle.low


def _strategy_row(candle: Candle) -> StrategyRow:
    return StrategyRow(date=candle.opened_at.isoformat(), close=candle.close)
