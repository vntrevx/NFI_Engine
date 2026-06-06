from __future__ import annotations

from nfi_engine.backtest.errors import BacktestError, BacktestErrorCode
from nfi_engine.backtest.models import (
    BacktestRequest,
    BacktestResult,
    BacktestSummary,
    EquityPoint,
    ReproducibilityMetadata,
    SimulationSettings,
    StrategySummary,
    TradeRecord,
)
from nfi_engine.backtest.runner import run_backtest
from nfi_engine.backtest.serialization import (
    BacktestPayload,
    MetadataPayload,
    metadata_to_payload,
    result_to_json_payload,
)

__all__ = [
    "BacktestError",
    "BacktestErrorCode",
    "BacktestPayload",
    "BacktestRequest",
    "BacktestResult",
    "BacktestSummary",
    "EquityPoint",
    "MetadataPayload",
    "ReproducibilityMetadata",
    "SimulationSettings",
    "StrategySummary",
    "TradeRecord",
    "metadata_to_payload",
    "result_to_json_payload",
    "run_backtest",
]
