from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class X7DataRequirements:
    base_timeframe: str
    informative_timeframes: tuple[str, ...]
    required_ohlcv_columns: tuple[str, ...]
    mandatory_external_dependencies: tuple[str, ...]


X7_DATA_REQUIREMENTS: Final = X7DataRequirements(
    base_timeframe="5m",
    informative_timeframes=("15m", "1h", "4h", "1d"),
    required_ohlcv_columns=("date", "open", "high", "low", "close", "volume"),
    mandatory_external_dependencies=(),
)
