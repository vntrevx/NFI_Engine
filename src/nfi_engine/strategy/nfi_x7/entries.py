from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum, unique
from typing import Final

from nfi_engine.strategy import (
    SignalColumns,
    StrategyFeatureName,
    StrategyFrame,
    StrategyRow,
)

LONG_ENTRY_TAG: Final = "x7-long-momentum-balanced"
SHORT_ENTRY_TAG: Final = "x7-short-momentum-fade"
ROC_1_FEATURE: Final = StrategyFeatureName("x7_base_roc_1")
RANGE_FEATURE: Final = StrategyFeatureName("x7_base_range_pct")
LONG_MIN_ROC: Final = Decimal("0.5")
SHORT_MAX_ROC: Final = Decimal("-1.0")
MAX_LONG_RANGE: Final = Decimal("6.0")
MAX_SHORT_RANGE: Final = Decimal("8.0")
MIN_ENTRY_ROWS: Final = 2


@unique
class X7EntryReason(StrEnum):
    LONG_MOMENTUM_BALANCED = "long_momentum_balanced"
    SHORT_MOMENTUM_FADE = "short_momentum_fade"
    WARMUP = "warmup"
    NO_ENTRY = "no_entry"


@dataclass(frozen=True, slots=True)
class X7EntryDecision:
    reason: X7EntryReason
    columns: SignalColumns


def apply_x7_entry_decision(frame: StrategyFrame) -> StrategyFrame:
    decision = build_x7_entry_decision(
        frame.last_visible_row(),
        visible_rows=len(frame.visible_rows()),
    )
    if decision.reason in (X7EntryReason.WARMUP, X7EntryReason.NO_ENTRY):
        return frame
    return frame.with_signal(index=-1, columns=decision.columns)


def build_x7_entry_decision(row: StrategyRow, *, visible_rows: int) -> X7EntryDecision:
    if visible_rows < MIN_ENTRY_ROWS:
        return _no_signal(X7EntryReason.WARMUP)
    roc = _feature_or_none(row=row, name=ROC_1_FEATURE)
    range_pct = _feature_or_none(row=row, name=RANGE_FEATURE)
    if roc is None or range_pct is None:
        return _no_signal(X7EntryReason.WARMUP)
    if roc >= LONG_MIN_ROC and range_pct <= MAX_LONG_RANGE:
        return X7EntryDecision(
            reason=X7EntryReason.LONG_MOMENTUM_BALANCED,
            columns=SignalColumns(enter_long=True, enter_tag=LONG_ENTRY_TAG),
        )
    if roc <= SHORT_MAX_ROC and range_pct <= MAX_SHORT_RANGE:
        return X7EntryDecision(
            reason=X7EntryReason.SHORT_MOMENTUM_FADE,
            columns=SignalColumns(enter_short=True, enter_tag=SHORT_ENTRY_TAG),
        )
    return _no_signal(X7EntryReason.NO_ENTRY)


def _feature_or_none(*, row: StrategyRow, name: StrategyFeatureName) -> Decimal | None:
    for feature in row.features:
        if feature.name == name:
            return feature.value
    return None


def _no_signal(reason: X7EntryReason) -> X7EntryDecision:
    return X7EntryDecision(reason=reason, columns=SignalColumns())
