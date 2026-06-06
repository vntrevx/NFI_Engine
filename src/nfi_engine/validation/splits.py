from __future__ import annotations

from nfi_engine.data import CandleBatch
from nfi_engine.validation.errors import ValidationError, ValidationErrorCode
from nfi_engine.validation.models import WalkForwardRole, WalkForwardWindow

MIN_SPLIT_COUNT = 3


def generate_walk_forward_splits(
    batch: CandleBatch,
    *,
    split_count: int,
) -> tuple[WalkForwardWindow, ...]:
    if split_count < MIN_SPLIT_COUNT:
        raise ValidationError(
            code=ValidationErrorCode.WALK_FORWARD_SPLIT_COUNT_INVALID,
            message="walk-forward splits must include train, validation, and test windows",
        )
    if len(batch.candles) < split_count:
        raise ValidationError(
            code=ValidationErrorCode.WALK_FORWARD_SPLIT_COUNT_INVALID,
            message="not enough candles for requested walk-forward split count",
        )
    windows = _windows(batch=batch, split_count=split_count)
    _reject_overlap(windows)
    return windows


def _windows(*, batch: CandleBatch, split_count: int) -> tuple[WalkForwardWindow, ...]:
    counts = _partition_counts(total=len(batch.candles), split_count=split_count)
    windows: tuple[WalkForwardWindow, ...] = ()
    start_index = 0
    for index, candle_count in enumerate(counts):
        end_index = start_index + candle_count
        window_candles = batch.candles[start_index:end_index]
        windows += (
            WalkForwardWindow(
                role=_role_for_index(index=index, split_count=split_count),
                start_index=start_index,
                end_index=end_index,
                start=window_candles[0].opened_at,
                end=window_candles[-1].opened_at,
                candle_count=candle_count,
            ),
        )
        start_index = end_index
    return windows


def _partition_counts(*, total: int, split_count: int) -> tuple[int, ...]:
    base = total // split_count
    remainder = total % split_count
    return tuple(base + (1 if index < remainder else 0) for index in range(split_count))


def _role_for_index(*, index: int, split_count: int) -> WalkForwardRole:
    if index == split_count - 1:
        return WalkForwardRole.TEST
    if index == split_count - 2:
        return WalkForwardRole.VALIDATION
    return WalkForwardRole.TRAIN


def _reject_overlap(windows: tuple[WalkForwardWindow, ...]) -> None:
    previous_end_index = 0
    for window in windows:
        if window.start_index < previous_end_index:
            raise ValidationError(
                code=ValidationErrorCode.WALK_FORWARD_SPLIT_OVERLAP,
                message="walk-forward split windows must not overlap",
            )
        previous_end_index = window.end_index
