from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from nfi_engine.domain import Candle, Price, TradingPair


@dataclass(frozen=True, slots=True)
class RawCandleColumns:
    pair: tuple[str, ...]
    timeframe: tuple[str, ...]
    opened_at: tuple[str, ...]
    open: tuple[str, ...]
    high: tuple[str, ...]
    low: tuple[str, ...]
    close: tuple[str, ...]
    volume: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CandleBatch:
    pair: TradingPair
    timeframe: str
    candles: tuple[Candle, ...]


@dataclass(frozen=True, slots=True)
class InformativeJoinRow:
    base_opened_at: datetime
    base_close: Price
    informative_opened_at: datetime
    informative_close: Price


@dataclass(frozen=True, slots=True)
class InformativeJoin:
    base_timeframe: str
    informative_timeframe: str
    rows: tuple[InformativeJoinRow, ...]
