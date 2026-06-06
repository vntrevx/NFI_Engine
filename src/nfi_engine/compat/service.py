from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from nfi_engine.compat.metadata import load_nfi_metadata
from nfi_engine.strategy import FreqtradeStrategyAdapter, load_freqtrade_strategy

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


@dataclass(frozen=True, slots=True)
class NfiCompatibilityResult:
    compatible: bool
    full_x7_parity: bool
    upstream_sha: str
    detected_callbacks: tuple[str, ...]
    unsupported_surfaces: tuple[str, ...]


def run_nfi_compatibility_check(strategy_spec: str) -> NfiCompatibilityResult:
    metadata = load_nfi_metadata()
    strategy = load_freqtrade_strategy(strategy_spec)
    inspection = FreqtradeStrategyAdapter.from_strategy(strategy).inspect()
    detected = frozenset(inspection.detected_callbacks)
    return NfiCompatibilityResult(
        compatible=REQUIRED_CALLBACKS.issubset(detected),
        full_x7_parity=metadata.full_x7_parity,
        upstream_sha=metadata.upstream_sha,
        detected_callbacks=inspection.detected_callbacks,
        unsupported_surfaces=UNSUPPORTED_SURFACES,
    )
