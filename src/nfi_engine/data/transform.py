from __future__ import annotations

# pyright: reportAny=false, reportUnknownArgumentType=false, reportUnknownMemberType=false
# pyright: reportUnknownVariableType=false, reportUnnecessaryIsInstance=false, reportUnreachable=false
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import polars as pl

from nfi_engine.data.errors import DataErrorCode, DataLoadError
from nfi_engine.data.models import CandleBatch, InformativeJoinRow, RawCandleColumns
from nfi_engine.domain import Candle, Price, Quantity, TradingPair


def candles_from_columns(
    *,
    pair: TradingPair,
    columns: RawCandleColumns,
    path: Path,
) -> tuple[Candle, ...]:
    return tuple(
        Candle(
            pair=pair,
            opened_at=parse_timestamp(columns.opened_at[index], path=path),
            open=Price(parse_decimal(columns.open[index], field_name="open", path=path)),
            high=Price(parse_decimal(columns.high[index], field_name="high", path=path)),
            low=Price(parse_decimal(columns.low[index], field_name="low", path=path)),
            close=Price(parse_decimal(columns.close[index], field_name="close", path=path)),
            volume=Quantity(parse_decimal(columns.volume[index], field_name="volume", path=path)),
        )
        for index in range(len(columns.opened_at))
    )


def parse_timestamp(raw: str, *, path: Path | None) -> datetime:
    normalized = raw.removesuffix("Z") + "+00:00" if raw.endswith("Z") else raw
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise DataLoadError(
            code=DataErrorCode.CANDLE_TIMESTAMP_INVALID,
            message=f"invalid opened_at timestamp: {raw}",
            path=path,
        ) from exc
    if parsed.tzinfo is None:
        raise DataLoadError(
            code=DataErrorCode.CANDLE_TIMESTAMP_INVALID,
            message=f"opened_at timestamp must include timezone: {raw}",
            path=path,
        )
    return parsed.astimezone(UTC)


def parse_decimal(raw: str, *, field_name: str, path: Path | None) -> Decimal:
    try:
        value = Decimal(raw)
    except ArithmeticError as exc:
        raise DataLoadError(
            code=DataErrorCode.CANDLE_DECIMAL_INVALID,
            message=f"{field_name} is not numeric",
            path=path,
        ) from exc
    if not value.is_finite():
        raise DataLoadError(
            code=DataErrorCode.CANDLE_DECIMAL_INVALID,
            message=f"{field_name} must be finite",
            path=path,
        )
    return value


def batch_to_polars(batch: CandleBatch) -> pl.DataFrame:
    return pl.DataFrame(
        {
            "opened_at": [candle.opened_at for candle in batch.candles],
            "open": [Decimal(candle.open) for candle in batch.candles],
            "high": [Decimal(candle.high) for candle in batch.candles],
            "low": [Decimal(candle.low) for candle in batch.candles],
            "close": [Decimal(candle.close) for candle in batch.candles],
            "volume": [Decimal(candle.volume) for candle in batch.candles],
        },
        schema_overrides={
            "opened_at": pl.Datetime(time_unit="us", time_zone="UTC"),
            "open": pl.Decimal(precision=38, scale=12),
            "high": pl.Decimal(precision=38, scale=12),
            "low": pl.Decimal(precision=38, scale=12),
            "close": pl.Decimal(precision=38, scale=12),
            "volume": pl.Decimal(precision=38, scale=12),
        },
    ).sort("opened_at")


def base_join_frame(batch: CandleBatch) -> pl.DataFrame:
    return (
        batch_to_polars(batch)
        .select(
            "opened_at",
            pl.col("close").alias("base_close"),
        )
        .sort("opened_at")
    )


def informative_join_frame(batch: CandleBatch) -> pl.DataFrame:
    return (
        batch_to_polars(batch)
        .select(
            "opened_at",
            pl.col("opened_at").alias("informative_opened_at"),
            pl.col("close").alias("informative_close"),
        )
        .sort("opened_at")
    )


def candles_from_numeric_frame(
    *,
    frame: pl.DataFrame,
    pair: TradingPair,
    path: Path | None,
) -> tuple[Candle, ...]:
    opened_at_values = datetime_column(frame=frame, column="opened_at", path=path)
    return tuple(
        Candle(
            pair=pair,
            opened_at=opened_at_values[index],
            open=Price(decimal_column_value(frame=frame, column="open", index=index, path=path)),
            high=Price(decimal_column_value(frame=frame, column="high", index=index, path=path)),
            low=Price(decimal_column_value(frame=frame, column="low", index=index, path=path)),
            close=Price(decimal_column_value(frame=frame, column="close", index=index, path=path)),
            volume=Quantity(
                decimal_column_value(frame=frame, column="volume", index=index, path=path),
            ),
        )
        for index in range(len(opened_at_values))
    )


def informative_rows_from_frame(frame: pl.DataFrame) -> tuple[InformativeJoinRow, ...]:
    base_opened_at_values = datetime_column(frame=frame, column="opened_at", path=None)
    base_close_values = decimal_column(frame=frame, column="base_close", path=None)
    informative_opened_at_values = datetime_column(
        frame=frame,
        column="informative_opened_at",
        path=None,
    )
    informative_close_values = decimal_column(frame=frame, column="informative_close", path=None)
    return tuple(
        InformativeJoinRow(
            base_opened_at=base_opened_at_values[index],
            base_close=Price(base_close_values[index]),
            informative_opened_at=informative_opened_at_values[index],
            informative_close=Price(informative_close_values[index]),
        )
        for index in range(len(base_opened_at_values))
    )


def datetime_column(*, frame: pl.DataFrame, column: str, path: Path | None) -> tuple[datetime, ...]:
    values: object = frame.get_column(column).to_list()
    if not isinstance(values, list):
        raise _informative_gap(column=column, path=path)
    return tuple(_datetime_value(value=value, column=column, path=path) for value in values)


def decimal_column(*, frame: pl.DataFrame, column: str, path: Path | None) -> tuple[Decimal, ...]:
    values: object = frame.get_column(column).to_list()
    if not isinstance(values, list):
        raise _informative_gap(column=column, path=path)
    return tuple(_decimal_value(value=value, column=column, path=path) for value in values)


def decimal_column_value(
    *,
    frame: pl.DataFrame,
    column: str,
    index: int,
    path: Path | None,
) -> Decimal:
    return decimal_column(frame=frame, column=column, path=path)[index]


def _datetime_value(*, value: object, column: str, path: Path | None) -> datetime:
    if isinstance(value, datetime):
        return value.astimezone(UTC)
    raise _informative_gap(column=column, path=path)


def _decimal_value(*, value: object, column: str, path: Path | None) -> Decimal:
    if isinstance(value, Decimal):
        return value
    raise _informative_gap(column=column, path=path)


def _informative_gap(*, column: str, path: Path | None) -> DataLoadError:
    return DataLoadError(
        code=DataErrorCode.CANDLE_INFORMATIVE_GAP,
        message=f"joined candle column has null or invalid values: {column}",
        path=path,
    )
