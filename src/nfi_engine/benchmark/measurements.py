from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from time import perf_counter

from nfi_engine.api.app import create_app
from nfi_engine.api.dashboard_models import DashboardSnapshotResponse
from nfi_engine.api.models import initial_log_entries
from nfi_engine.benchmark.backtest_workload import (
    BACKTEST_WORKLOAD_CANDLES,
    build_backtest_workload_request,
    run_backtest_workload,
)
from nfi_engine.benchmark.models import BenchmarkMeasurement, MeasurementInput
from nfi_engine.benchmark.x7_measurements import x7_measurements
from nfi_engine.config import Locale, RuntimeSettings, load_runtime_settings
from nfi_engine.dashboard import (
    DashboardReadModels,
    StaticDashboardReadStore,
    build_dashboard_snapshot,
)
from nfi_engine.domain import TradingMode
from nfi_engine.paper import BotState
from nfi_engine.preflight.service import run_preflight
from nfi_engine.profiles.catalog import default_profile_name
from nfi_engine.setup import RiskPreset, SetupIntent, SetupRequest, write_setup_config
from nfi_engine.ui import render_home_page
from nfi_engine.ui.chart import render_dashboard_chart_panel
from nfi_engine.ui.home_context import HomeRuntimeContext


def m2_measurements(
    *,
    settings: RuntimeSettings,
    config: Path,
    samples: int,
) -> tuple[BenchmarkMeasurement, ...]:
    return (
        _startup_measurement(settings=settings, config=config, samples=samples),
        _dashboard_snapshot_measurement(settings=settings, config=config, samples=samples),
        _home_render_measurement(settings=settings, samples=samples),
        _chart_render_measurement(settings=settings, samples=samples),
        _backtest_workload_measurement(samples=samples),
        *x7_measurements(samples=samples),
        _install_smoke_measurement(samples=samples),
    )


def _startup_measurement(
    *,
    settings: RuntimeSettings,
    config: Path,
    samples: int,
) -> BenchmarkMeasurement:
    duration, payload = _sample(
        samples=samples,
        action=lambda: _create_app_payload(settings=settings, config=config),
    )
    return _measurement(
        MeasurementInput(
            name="startup_smoke",
            workflow="create_app with static dashboard store",
            samples=samples,
            duration_ms=duration,
            budget_ms=1_000.0,
            data_label="examples-futures-paper-empty-store",
            payload_bytes=payload,
        ),
    )


def _dashboard_snapshot_measurement(
    *,
    settings: RuntimeSettings,
    config: Path,
    samples: int,
) -> BenchmarkMeasurement:
    logs = initial_log_entries()
    readiness = run_preflight(
        settings=settings,
        profile_name=default_profile_name(settings),
        config_path=config,
    )
    read_models = DashboardReadModels.empty()
    duration, payload = _sample(
        samples=samples,
        action=lambda: len(
            DashboardSnapshotResponse.from_snapshot(
                build_dashboard_snapshot(
                    settings=settings,
                    bot_state=BotState.STOPPED,
                    readiness=readiness,
                    logs=logs,
                    read_models=read_models,
                ),
            )
            .model_dump_json()
            .encode(),
        ),
    )
    return _measurement(
        MeasurementInput(
            name="dashboard_snapshot_latency",
            workflow="build and serialize dashboard snapshot contract",
            samples=samples,
            duration_ms=duration,
            budget_ms=50.0,
            data_label="fixture-empty",
            payload_bytes=payload,
        ),
    )


def _home_render_measurement(*, settings: RuntimeSettings, samples: int) -> BenchmarkMeasurement:
    duration, payload = _sample(
        samples=samples,
        action=lambda: len(
            render_home_page(
                settings=settings,
                logs=initial_log_entries(),
                runtime=HomeRuntimeContext(),
            ).encode("utf-8"),
        ),
    )
    return _measurement(
        MeasurementInput(
            name="home_render_smoke",
            workflow="render / home HTML",
            samples=samples,
            duration_ms=duration,
            budget_ms=50.0,
            data_label="server-render-empty-readiness",
            payload_bytes=payload,
        ),
    )


def _chart_render_measurement(*, settings: RuntimeSettings, samples: int) -> BenchmarkMeasurement:
    duration, payload = _sample(
        samples=samples,
        action=lambda: len(
            render_dashboard_chart_panel(
                exchange=settings.exchange.name,
                trading_mode=settings.exchange.trading_mode.value,
                locale=Locale.EN,
            ).encode(),
        ),
    )
    return _measurement(
        MeasurementInput(
            name="chart_render_smoke",
            workflow="render dashboard chart shell",
            samples=samples,
            duration_ms=duration,
            budget_ms=5.0,
            data_label="chart-shell",
            payload_bytes=payload,
        ),
    )


def _backtest_workload_measurement(*, samples: int) -> BenchmarkMeasurement:
    request = build_backtest_workload_request()
    duration, payload = _sample(
        samples=samples,
        action=lambda: run_backtest_workload(request),
    )
    return _measurement(
        MeasurementInput(
            name="backtest_720_candle_latency",
            workflow="run deterministic 720-candle backtest with clean-room smoke strategy",
            samples=samples,
            duration_ms=duration,
            budget_ms=1_000.0,
            data_label=f"synthetic-{BACKTEST_WORKLOAD_CANDLES}-5m-flat",
            payload_bytes=payload,
        ),
    )


def _install_smoke_measurement(*, samples: int) -> BenchmarkMeasurement:
    duration, payload = _sample(samples=samples, action=_install_smoke_payload)
    return _measurement(
        MeasurementInput(
            name="install_smoke",
            workflow="setup config dry-run plus config validate",
            samples=samples,
            duration_ms=duration,
            budget_ms=1_000.0,
            data_label="setup-dry-run",
            payload_bytes=payload,
        ),
    )


def _sample(*, samples: int, action: Callable[[], int | None]) -> tuple[float, int | None]:
    durations: list[float] = []
    payload_bytes: int | None = None
    for _ in range(samples):
        started_at = perf_counter()
        payload_bytes = action()
        durations.append((perf_counter() - started_at) * 1000)
    return (_p95(durations), payload_bytes)


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    index = max(0, int((len(ordered) * 0.95) - 1))
    return round(ordered[index], 3)


def _create_app_payload(*, settings: RuntimeSettings, config: Path) -> int:
    app = create_app(
        settings=settings,
        config_path=config,
        dashboard_store=StaticDashboardReadStore(),
    )
    return len(app.routes)


def _install_smoke_payload() -> int:
    with tempfile.TemporaryDirectory(prefix="nfi-engine-benchmark-") as directory:
        runtime_dir = Path(directory)
        config_path = runtime_dir / "config" / "futures-paper.yaml"
        plan = write_setup_config(
            request=SetupRequest(
                exchange="bybit",
                trading_mode=TradingMode.FUTURES,
                intent=SetupIntent.TESTNET,
                risk_preset=RiskPreset.BALANCED,
            ),
            config_path=config_path,
            overwrite=True,
        )
        load_runtime_settings(config_path)
        env_file = runtime_dir / "docker.env"
        env_file.write_text("NFI_ENGINE_API_TOKEN=redacted\n", encoding="utf-8")
        env_file.chmod(0o600)
        return len(plan.redacted_config_text.encode())


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
