from __future__ import annotations

import os
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from nfi_engine.benchmark.measurements import m2_measurements
from nfi_engine.benchmark.models import (
    BenchmarkEnvironment,
    BenchmarkError,
    BenchmarkReport,
    FreqtradeComparison,
)
from nfi_engine.config import DatabaseSettings, load_runtime_settings

DEFAULT_REGRESSION_BUDGET_PERCENT: Final = 5.0


def build_m2_report(
    *,
    config: Path,
    samples: int,
    allow_regression: bool,
    regression_reason: str | None,
) -> BenchmarkReport:
    if samples < 1:
        raise BenchmarkError(code="BENCHMARK_SAMPLE_COUNT_INVALID", message="samples must be >= 1")
    settings = load_runtime_settings(config).model_copy(
        update={"database": DatabaseSettings(url="sqlite+aiosqlite:///:memory:")},
    )
    return BenchmarkReport(
        schema_version=1,
        benchmark="m2",
        generated_at=_utc_now(),
        environment=_environment(),
        regression_budget_percent=DEFAULT_REGRESSION_BUDGET_PERCENT,
        allow_regression=allow_regression,
        regression_reason=regression_reason,
        measurements=m2_measurements(settings=settings, config=config, samples=samples),
        freqtrade_comparison=FreqtradeComparison(
            freqtrade_available=False,
            freqtrade_version=None,
            workflow="not-run",
            nfi_engine_result=None,
            freqtrade_result=None,
            ratio=None,
            claim_allowed=False,
        ),
    )


def regression_messages(report: BenchmarkReport, baseline: Path | None) -> tuple[str, ...]:
    if baseline is None:
        return ()
    baseline_report = BenchmarkReport.model_validate_json(baseline.read_text(encoding="utf-8"))
    baseline_by_name = {
        measurement.name: measurement for measurement in baseline_report.measurements
    }
    messages: list[str] = []
    for measurement in report.measurements:
        baseline_measurement = baseline_by_name.get(measurement.name)
        if baseline_measurement is None:
            continue
        allowed = baseline_measurement.duration_ms * (1 + (report.regression_budget_percent / 100))
        if measurement.duration_ms > allowed:
            messages.append(
                f"{measurement.name} {measurement.duration_ms:.3f}ms > {allowed:.3f}ms",
            )
    return tuple(messages)


def write_report(path: Path, report: BenchmarkReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")


def _environment() -> BenchmarkEnvironment:
    return BenchmarkEnvironment(
        python=platform.python_version(),
        platform=platform.platform(),
        machine=platform.machine(),
        processor=platform.processor(),
        cpu_count=os.cpu_count() or 1,
    )


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")
