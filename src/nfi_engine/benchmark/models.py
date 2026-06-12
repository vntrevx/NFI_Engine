from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


class BenchmarkEnvironment(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    python: str
    platform: str
    machine: str
    processor: str
    cpu_count: int


class BenchmarkMeasurement(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    name: str
    workflow: str
    samples: int
    duration_ms: float
    budget_ms: float
    status: str
    data_label: str
    payload_bytes: int | None = None


class FreqtradeComparison(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    freqtrade_available: bool
    freqtrade_version: str | None
    workflow: str
    nfi_engine_result: float | None
    freqtrade_result: float | None
    ratio: float | None
    claim_allowed: bool


class BenchmarkReport(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    schema_version: int
    benchmark: str
    generated_at: str
    environment: BenchmarkEnvironment
    regression_budget_percent: float
    allow_regression: bool
    regression_reason: str | None
    measurements: tuple[BenchmarkMeasurement, ...]
    freqtrade_comparison: FreqtradeComparison


@dataclass(frozen=True, slots=True)
class BenchmarkError(Exception):
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class MeasurementInput:
    name: str
    workflow: str
    samples: int
    duration_ms: float
    budget_ms: float
    data_label: str
    payload_bytes: int | None
