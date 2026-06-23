from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class X7StrategyMetadata:
    name: str
    strategy_class_name: str
    observed_upstream_version: str
    base_timeframe: str
    provenance_evidence_path: str


X7_METADATA: Final = X7StrategyMetadata(
    name="NFI_X7_NATIVE",
    strategy_class_name="X7NativeStrategy",
    observed_upstream_version="v17.4.258",
    base_timeframe="5m",
    provenance_evidence_path=(
        ".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-01-provenance-coverage.md"
    ),
)
