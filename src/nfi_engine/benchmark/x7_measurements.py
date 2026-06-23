from __future__ import annotations

from collections.abc import Callable
from time import perf_counter

from nfi_engine.benchmark.models import BenchmarkMeasurement, MeasurementInput
from nfi_engine.benchmark.x7_workloads import (
    inspect_x7_strategy_payload,
    load_x7_benchmark_settings,
    run_x7_backtest_workload,
    run_x7_feature_graph_workload,
    run_x7_paper_workload,
)


def x7_measurements(*, samples: int) -> tuple[BenchmarkMeasurement, ...]:
    settings = load_x7_benchmark_settings()
    return (
        _measurement(
            MeasurementInput(
                name="x7_strategy_inspect_latency",
                workflow="inspect native X7 callbacks and semantic coverage ledger",
                samples=samples,
                duration_ms=_duration(
                    samples=samples,
                    action=lambda: inspect_x7_strategy_payload(settings),
                ),
                budget_ms=50.0,
                data_label="examples-x7-futures-paper",
                payload_bytes=None,
            ),
        ),
        _measurement(
            MeasurementInput(
                name="x7_feature_graph_latency",
                workflow="build native X7 feature graph from synthetic OHLCV and informatives",
                samples=samples,
                duration_ms=_duration(samples=samples, action=run_x7_feature_graph_workload),
                budget_ms=100.0,
                data_label="synthetic-x7-5m-15m-1h",
                payload_bytes=None,
            ),
        ),
        _measurement(
            MeasurementInput(
                name="x7_backtest_sample_latency",
                workflow="run deterministic native X7 backtest sample without Freqtrade runtime",
                samples=samples,
                duration_ms=_duration(
                    samples=samples,
                    action=lambda: run_x7_backtest_workload(settings),
                ),
                budget_ms=1_000.0,
                data_label="synthetic-120-x7-5m-futures",
                payload_bytes=None,
            ),
        ),
        _measurement(
            MeasurementInput(
                name="x7_paper_sample_latency",
                workflow="run native X7 paper sample with temp SQLite and no live orders",
                samples=samples,
                duration_ms=_duration(
                    samples=samples,
                    action=lambda: run_x7_paper_workload(settings),
                ),
                budget_ms=1_000.0,
                data_label="synthetic-24-x7-paper-ticks",
                payload_bytes=None,
            ),
        ),
    )


def _duration(*, samples: int, action: Callable[[], int]) -> float:
    durations: list[float] = []
    for _ in range(samples):
        started_at = perf_counter()
        action()
        durations.append((perf_counter() - started_at) * 1000)
    return _p95(durations)


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    index = max(0, int((len(ordered) * 0.95) - 1))
    return round(ordered[index], 3)


def _measurement(measurement: MeasurementInput) -> BenchmarkMeasurement:
    return BenchmarkMeasurement(
        name=measurement.name,
        workflow=measurement.workflow,
        samples=measurement.samples,
        duration_ms=measurement.duration_ms,
        budget_ms=measurement.budget_ms,
        status="pass" if measurement.duration_ms <= measurement.budget_ms else "warn",
        data_label=measurement.data_label,
        payload_bytes=measurement.payload_bytes,
    )
