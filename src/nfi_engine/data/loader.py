from __future__ import annotations

# pyright: reportAny=false, reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnnecessaryIsInstance=false, reportUnreachable=false
import re
from datetime import datetime, timedelta
from pathlib import Path
from re import Pattern
from typing import Final

import polars as pl
from polars.exceptions import PolarsError, SchemaFieldNotFoundError

from nfi_engine.data.errors import DataErrorCode, DataLoadError
from nfi_engine.data.models import CandleBatch, InformativeJoin, RawCandleColumns
from nfi_engine.data.transform import (
    base_join_frame,
    batch_to_polars,
    candles_from_columns,
    candles_from_numeric_frame,
    informative_join_frame,
    informative_rows_from_frame,
)
from nfi_engine.domain import Candle, TradingMode, TradingPair

REQUIRED_COLUMNS: Final = (
    "pair",
    "timeframe",
    "opened_at",
    "open",
    "high",
    "low",
    "close",
    "volume",
)
TIMEFRAME_PATTERN: Final[Pattern[str]] = re.compile(r"^(?P<count>[1-9][0-9]*)(?P<unit>m|h|d)$")
DECIMAL_TYPE: Final = pl.Decimal(precision=38, scale=12)
MIN_CANDLES_FOR_INTERVAL_VALIDATION: Final = 2
SCHEMA_OVERRIDES: Final[dict[str, type[pl.String]]] = {
    str(column): pl.String for column in REQUIRED_COLUMNS
}


def load_candle_batch(path: Path) -> CandleBatch:
    raw_frame = _read_raw_frame(path)
    _require_columns(raw_frame, path)
    if raw_frame.is_empty():
        raise DataLoadError(
            code=DataErrorCode.CANDLE_EMPTY,
            message="candle file has no rows",
            path=path,
        )
    columns = _columns_from_frame(raw_frame.select(REQUIRED_COLUMNS).sort("opened_at"), path)
    pair = TradingPair.parse(
        _require_single_value(columns.pair, field_name="pair", path=path),
        _trading_mode_for_pair(columns.pair[0]),
    )
    timeframe = _require_single_value(columns.timeframe, field_name="timeframe", path=path)
    candles = candles_from_columns(
        pair=pair,
        columns=columns,
        path=path,
    )
    _reject_duplicate_timestamps(candles=candles, path=path)
    _validate_timeframe(candles=candles, timeframe=timeframe, path=path)
    return CandleBatch(pair=pair, timeframe=timeframe, candles=candles)


def align_candle_batch(batch: CandleBatch, *, target_timeframe: str) -> CandleBatch:
    source_delta = parse_timeframe(batch.timeframe)
    target_delta = parse_timeframe(target_timeframe)
    if _is_invalid_alignment_target(source_delta=source_delta, target_delta=target_delta):
        raise DataLoadError(
            code=DataErrorCode.CANDLE_TIMEFRAME_MISMATCH,
            message=f"target timeframe {target_timeframe} must be a multiple of {batch.timeframe}",
        )
    aligned_frame = (
        batch_to_polars(batch)
        .group_by_dynamic("opened_at", every=target_timeframe, closed="left", label="left")
        .agg(
            pl.col("open").first(),
            pl.col("high").max(),
            pl.col("low").min(),
            pl.col("close").last(),
            pl.col("volume").sum(),
        )
        .sort("opened_at")
    )
    candles = candles_from_numeric_frame(frame=aligned_frame, pair=batch.pair, path=None)
    return CandleBatch(pair=batch.pair, timeframe=target_timeframe, candles=candles)


def join_informative_candles(
    *,
    base: CandleBatch,
    informative: CandleBatch,
) -> InformativeJoin:
    if base.pair != informative.pair:
        raise DataLoadError(
            code=DataErrorCode.CANDLE_PAIR_MISMATCH,
            message="base and informative candle batches must use the same pair",
        )
    joined_frame = base_join_frame(base).join_asof(
        informative_join_frame(informative),
        on="opened_at",
        strategy="backward",
    )
    rows = informative_rows_from_frame(joined_frame)
    return InformativeJoin(
        base_timeframe=base.timeframe,
        informative_timeframe=informative.timeframe,
        rows=rows,
    )


def parse_timeframe(timeframe: str) -> timedelta:
    match_result = TIMEFRAME_PATTERN.fullmatch(timeframe)
    if match_result is None:
        raise DataLoadError(
            code=DataErrorCode.CANDLE_TIMEFRAME_MISMATCH,
            message=f"unsupported timeframe: {timeframe}",
        )
    count = int(match_result.group("count"))
    match match_result.group("unit"):
        case "m":
            return timedelta(minutes=count)
        case "h":
            return timedelta(hours=count)
        case "d":
            return timedelta(days=count)
        case _:
            raise DataLoadError(
                code=DataErrorCode.CANDLE_TIMEFRAME_MISMATCH,
                message=f"unsupported timeframe: {timeframe}",
            )


def _read_raw_frame(path: Path) -> pl.DataFrame:
    if not path.exists():
        raise DataLoadError(
            code=DataErrorCode.CANDLE_FILE_NOT_FOUND,
            message="candle file does not exist",
            path=path,
        )
    try:
        return pl.read_ndjson(path, schema_overrides=SCHEMA_OVERRIDES)
    except SchemaFieldNotFoundError as exc:
        raise DataLoadError(
            code=DataErrorCode.CANDLE_SCHEMA_MISSING_COLUMN,
            message=f"missing candle column: {exc}",
            path=path,
        ) from exc
    except (OSError, PolarsError) as exc:
        raise DataLoadError(
            code=DataErrorCode.CANDLE_READ_FAILED,
            message="candle file could not be read as ndjson",
            path=path,
        ) from exc


def _require_columns(frame: pl.DataFrame, path: Path) -> None:
    missing = tuple(column for column in REQUIRED_COLUMNS if column not in frame.columns)
    if len(missing) > 0:
        raise DataLoadError(
            code=DataErrorCode.CANDLE_SCHEMA_MISSING_COLUMN,
            message=f"missing candle columns: {','.join(missing)}",
            path=path,
        )


def _columns_from_frame(frame: pl.DataFrame, path: Path) -> RawCandleColumns:
    return RawCandleColumns(
        pair=_string_column(frame=frame, column="pair", path=path),
        timeframe=_string_column(frame=frame, column="timeframe", path=path),
        opened_at=_string_column(frame=frame, column="opened_at", path=path),
        open=_string_column(frame=frame, column="open", path=path),
        high=_string_column(frame=frame, column="high", path=path),
        low=_string_column(frame=frame, column="low", path=path),
        close=_string_column(frame=frame, column="close", path=path),
        volume=_string_column(frame=frame, column="volume", path=path),
    )


def _string_column(*, frame: pl.DataFrame, column: str, path: Path) -> tuple[str, ...]:
    values: object = frame.get_column(column).to_list()
    if not isinstance(values, list):
        raise _schema_error(path=path, message=f"column is not list-like: {column}")
    return tuple(_string_value(value=value, column=column, path=path) for value in values)


def _string_value(*, value: object, column: str, path: Path) -> str:
    if isinstance(value, str):
        return value
    raise _schema_error(path=path, message=f"column {column} must contain strings")


def _schema_error(*, path: Path, message: str) -> DataLoadError:
    return DataLoadError(
        code=DataErrorCode.CANDLE_SCHEMA_MISSING_COLUMN,
        message=message,
        path=path,
    )


def _trading_mode_for_pair(pair: str) -> TradingMode:
    if ":" in pair:
        return TradingMode.FUTURES
    return TradingMode.SPOT


def _require_single_value(values: tuple[str, ...], *, field_name: str, path: Path) -> str:
    unique_values = frozenset(values)
    if len(unique_values) != 1:
        raise DataLoadError(
            code=DataErrorCode.CANDLE_SCHEMA_MISSING_COLUMN,
            message=f"candle file must contain one {field_name}",
            path=path,
        )
    return values[0]


def _is_invalid_alignment_target(*, source_delta: timedelta, target_delta: timedelta) -> bool:
    if target_delta < source_delta:
        return True
    return target_delta.total_seconds() % source_delta.total_seconds() != 0


def _reject_duplicate_timestamps(*, candles: tuple[Candle, ...], path: Path) -> None:
    seen: set[datetime] = set()
    for candle in candles:
        if candle.opened_at in seen:
            raise DataLoadError(
                code=DataErrorCode.CANDLE_DUPLICATE_TIMESTAMP,
                message=f"duplicate opened_at timestamp: {candle.opened_at.isoformat()}",
                path=path,
            )
        seen.add(candle.opened_at)


def _validate_timeframe(
    *,
    candles: tuple[Candle, ...],
    timeframe: str,
    path: Path,
) -> None:
    if len(candles) < MIN_CANDLES_FOR_INTERVAL_VALIDATION:
        return
    expected_delta = parse_timeframe(timeframe)
    previous = candles[0].opened_at
    for candle in candles[1:]:
        if candle.opened_at - previous != expected_delta:
            raise DataLoadError(
                code=DataErrorCode.CANDLE_TIMEFRAME_MISMATCH,
                message=f"candles are not aligned to timeframe {timeframe}",
                path=path,
            )
        previous = candle.opened_at
