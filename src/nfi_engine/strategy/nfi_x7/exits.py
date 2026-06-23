from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum, unique
from typing import Final, assert_never

from nfi_engine.strategy import (
    SignalColumns,
    StrategyFeatureName,
    StrategyFrame,
    StrategyRow,
    StrategyTrade,
)
from nfi_engine.strategy.nfi_x7.entries import RANGE_FEATURE, ROC_1_FEATURE

LONG_EXIT_TAG: Final = "x7-exit-long-momentum-cooldown"
SHORT_EXIT_TAG: Final = "x7-exit-short-momentum-cooldown"
LONG_EXIT_MAX_ROC: Final = Decimal("-0.50")
SHORT_EXIT_MIN_ROC: Final = Decimal("0.25")
MAX_EXIT_RANGE: Final = Decimal("6.0")
MIN_EXIT_ROWS: Final = 3


@unique
class X7ExitReason(StrEnum):
    LONG_MOMENTUM_COOLDOWN = "long_momentum_cooldown"
    SHORT_MOMENTUM_COOLDOWN = "short_momentum_cooldown"
    WARMUP = "warmup"
    NO_EXIT = "no_exit"


@unique
class X7CustomExitReason(StrEnum):
    FEATURE_CONTEXT_REQUIRED = "feature_context_required"


@dataclass(frozen=True, slots=True)
class X7ExitDecision:
    reason: X7ExitReason
    columns: SignalColumns


@dataclass(frozen=True, slots=True)
class X7CustomExitDecision:
    reason: X7CustomExitReason
    exit_reason: str | None


def apply_x7_exit_decision(frame: StrategyFrame) -> StrategyFrame:
    decision = build_x7_exit_decision(
        frame.last_visible_row(),
        visible_rows=len(frame.visible_rows()),
    )
    match decision.reason:
        case X7ExitReason.WARMUP | X7ExitReason.NO_EXIT:
            return frame
        case X7ExitReason.LONG_MOMENTUM_COOLDOWN | X7ExitReason.SHORT_MOMENTUM_COOLDOWN:
            return frame.with_signal(index=-1, columns=decision.columns)
        case unreachable:
            assert_never(unreachable)


def build_x7_exit_decision(row: StrategyRow, *, visible_rows: int) -> X7ExitDecision:
    if visible_rows < MIN_EXIT_ROWS:
        return _no_signal(X7ExitReason.WARMUP)
    roc = _feature_or_none(row=row, name=ROC_1_FEATURE)
    range_pct = _feature_or_none(row=row, name=RANGE_FEATURE)
    if roc is None or range_pct is None:
        return _no_signal(X7ExitReason.WARMUP)
    if range_pct > MAX_EXIT_RANGE:
        return _no_signal(X7ExitReason.NO_EXIT)
    if roc <= LONG_EXIT_MAX_ROC:
        return X7ExitDecision(
            reason=X7ExitReason.LONG_MOMENTUM_COOLDOWN,
            columns=SignalColumns(exit_long=True, exit_tag=LONG_EXIT_TAG),
        )
    if roc >= SHORT_EXIT_MIN_ROC:
        return X7ExitDecision(
            reason=X7ExitReason.SHORT_MOMENTUM_COOLDOWN,
            columns=SignalColumns(exit_short=True, exit_tag=SHORT_EXIT_TAG),
        )
    return _no_signal(X7ExitReason.NO_EXIT)


def build_x7_custom_exit_decision(_trade: StrategyTrade) -> X7CustomExitDecision:
    return X7CustomExitDecision(
        reason=X7CustomExitReason.FEATURE_CONTEXT_REQUIRED,
        exit_reason=None,
    )


def _feature_or_none(*, row: StrategyRow, name: StrategyFeatureName) -> Decimal | None:
    for feature in row.features:
        if feature.name == name:
            return feature.value
    return None


def _no_signal(reason: X7ExitReason) -> X7ExitDecision:
    return X7ExitDecision(reason=reason, columns=SignalColumns())
