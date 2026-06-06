from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from nfi_engine.backtest.errors import BacktestError, BacktestErrorCode
from nfi_engine.backtest.models import SimulationSettings
from nfi_engine.config import RuntimeSettings
from nfi_engine.data import CandleBatch
from nfi_engine.domain import TradingMode

DEFAULT_SPOT_CANDLES: Final = Path("tests/fixtures/candles/btc_usdt_5m.jsonl")
DEFAULT_FUTURES_CANDLES: Final = Path("tests/fixtures/candles/btc_usdt_usdt_futures_5m.jsonl")


@dataclass(frozen=True, slots=True)
class Timerange:
    start: datetime | None
    end: datetime | None


def simulation_settings_from_runtime(settings: RuntimeSettings) -> SimulationSettings:
    return SimulationSettings(
        trading_mode=settings.exchange.trading_mode,
        starting_balance=settings.backtest.starting_balance_usdt,
        stake_amount=settings.risk.stake_usdt,
        fee_rate=settings.backtest.fee_rate,
        slippage_rate=settings.backtest.slippage_rate,
        max_open_trades=settings.backtest.max_open_trades,
        leverage=settings.risk.leverage,
        liquidation_buffer=settings.risk.liquidation_buffer,
        stoploss_pct=settings.backtest.stoploss_pct,
    )


def config_digest(settings: RuntimeSettings, *, timerange: str | None) -> str:
    payload = settings.model_dump_json() + f"|timerange={timerange or ''}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def default_candle_path(settings: RuntimeSettings) -> Path:
    match settings.exchange.trading_mode:
        case TradingMode.SPOT:
            return DEFAULT_SPOT_CANDLES
        case TradingMode.FUTURES:
            return DEFAULT_FUTURES_CANDLES


def parse_timerange(raw: str | None) -> Timerange:
    if raw is None:
        return Timerange(start=None, end=None)
    start_raw, separator, end_raw = raw.partition(":")
    if separator == "":
        return Timerange(start=_parse_datetime(start_raw), end=None)
    return Timerange(
        start=_parse_datetime(start_raw) if start_raw else None,
        end=_parse_datetime(end_raw) if end_raw else None,
    )


def filter_timerange(batch: CandleBatch, timerange: Timerange) -> CandleBatch:
    filtered = tuple(
        candle for candle in batch.candles if _inside_timerange(candle.opened_at, timerange)
    )
    return CandleBatch(pair=batch.pair, timeframe=batch.timeframe, candles=filtered)


def _inside_timerange(opened_at: datetime, timerange: Timerange) -> bool:
    if timerange.start is not None and opened_at < timerange.start:
        return False
    return timerange.end is None or opened_at < timerange.end


def _parse_datetime(raw: str) -> datetime:
    try:
        parsed = _parse_iso_datetime(raw)
    except ValueError as exc:
        raise BacktestError(
            code=BacktestErrorCode.BACKTEST_TIMERANGE_INVALID,
            message=f"invalid timerange datetime: {raw}",
        ) from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _parse_iso_datetime(raw: str) -> datetime:
    if len(raw) == len("YYYY-MM-DD"):
        return datetime.fromisoformat(raw).replace(tzinfo=UTC)
    return datetime.fromisoformat(raw)
