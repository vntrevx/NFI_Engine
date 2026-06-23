from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

from nfi_engine.compat.metadata import load_nfi_metadata
from nfi_engine.strategy import (
    CallbackSupportLevel,
    FreqtradeStrategyAdapter,
    StrategyCallbackSupport,
    load_freqtrade_strategy,
)

REQUIRED_CALLBACKS: Final = frozenset(
    (
        "populate_indicators",
        "populate_entry_trend",
        "populate_exit_trend",
    ),
)
UNSUPPORTED_SURFACES: Final = (
    "full_x7_strategy_import",
    "upstream_strategy_vendoring",
    "full_x7_parity_claim",
)


class CallbackCompatibility(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    level: CallbackSupportLevel
    detected: bool
    reason: str


class NfiCompatibilityReport(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    strategy_name: str
    compatible: bool
    full_x7_parity: bool
    upstream_sha: str
    detected_callbacks: tuple[str, ...]
    supported_callbacks: tuple[str, ...]
    partial_callbacks: tuple[str, ...]
    excluded_callbacks: tuple[str, ...]
    excluded_surfaces: tuple[str, ...]
    unsupported_surfaces: tuple[str, ...]
    callback_support: tuple[CallbackCompatibility, ...]
    clean_room: bool


@dataclass(frozen=True, slots=True)
class NfiCompatibilityResult:
    strategy_name: str
    compatible: bool
    full_x7_parity: bool
    upstream_sha: str
    detected_callbacks: tuple[str, ...]
    supported_callbacks: tuple[str, ...]
    partial_callbacks: tuple[str, ...]
    excluded_callbacks: tuple[str, ...]
    excluded_surfaces: tuple[str, ...]
    unsupported_surfaces: tuple[str, ...]
    callback_support: tuple[StrategyCallbackSupport, ...]
    clean_room: bool

    def to_report(self) -> NfiCompatibilityReport:
        return NfiCompatibilityReport(
            strategy_name=self.strategy_name,
            compatible=self.compatible,
            full_x7_parity=self.full_x7_parity,
            upstream_sha=self.upstream_sha,
            detected_callbacks=self.detected_callbacks,
            supported_callbacks=self.supported_callbacks,
            partial_callbacks=self.partial_callbacks,
            excluded_callbacks=self.excluded_callbacks,
            excluded_surfaces=self.excluded_surfaces,
            unsupported_surfaces=self.unsupported_surfaces,
            callback_support=_report_callbacks(self.callback_support),
            clean_room=self.clean_room,
        )


def run_nfi_compatibility_check(strategy_spec: str) -> NfiCompatibilityResult:
    metadata = load_nfi_metadata()
    strategy = load_freqtrade_strategy(strategy_spec)
    inspection = FreqtradeStrategyAdapter.from_strategy(strategy).inspect()
    detected = frozenset(inspection.detected_callbacks)
    excluded_callbacks = _callback_names_by_level(
        inspection.callback_support,
        CallbackSupportLevel.EXCLUDED,
        detected_only=True,
    )
    return NfiCompatibilityResult(
        strategy_name=inspection.name,
        compatible=REQUIRED_CALLBACKS.issubset(detected) and len(excluded_callbacks) == 0,
        full_x7_parity=metadata.full_x7_parity,
        upstream_sha=metadata.upstream_sha,
        detected_callbacks=inspection.detected_callbacks,
        supported_callbacks=_callback_names_by_level(
            inspection.callback_support,
            CallbackSupportLevel.SUPPORTED,
            detected_only=True,
        ),
        partial_callbacks=_callback_names_by_level(
            inspection.callback_support,
            CallbackSupportLevel.PARTIAL,
            detected_only=True,
        ),
        excluded_callbacks=excluded_callbacks,
        excluded_surfaces=UNSUPPORTED_SURFACES,
        unsupported_surfaces=UNSUPPORTED_SURFACES,
        callback_support=inspection.callback_support,
        clean_room=True,
    )


def _callback_names_by_level(
    support: tuple[StrategyCallbackSupport, ...],
    level: CallbackSupportLevel,
    *,
    detected_only: bool,
) -> tuple[str, ...]:
    return tuple(
        item.name
        for item in support
        if item.level is level and (item.detected or not detected_only)
    )


def _report_callbacks(
    support: tuple[StrategyCallbackSupport, ...],
) -> tuple[CallbackCompatibility, ...]:
    return tuple(
        CallbackCompatibility(
            name=item.name,
            level=item.level,
            detected=item.detected,
            reason=item.reason,
        )
        for item in support
    )
