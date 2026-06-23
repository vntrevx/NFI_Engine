from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final, TypedDict

from pydantic import TypeAdapter

from nfi_engine.strategy.nfi_x7 import LONG_ENTRY_TAG

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
X7_CONFIG: Final = "examples/x7-futures-paper.yaml"
X7_PREFLIGHT_BLOCKED_CONFIG: Final = "tests/fixtures/config/x7-futures-risk-blocked.yaml"
X7_STRATEGY: Final = "nfi_engine.strategy.nfi_x7:X7NativeStrategy"


class StrategyPayload(TypedDict):
    name: str


class CoverageModulePayload(TypedDict):
    name: str
    status: str
    evidence_path: str
    blocker: str | None


class CoveragePayload(TypedDict):
    covered_modules: list[str]
    pending_modules: list[str]
    is_full_semantic_coverage: bool
    modules: list[CoverageModulePayload]


class StrategyInspectPayload(TypedDict):
    strategy_name: str
    semantic_coverage: CoveragePayload


class TimelineStepPayload(TypedDict):
    pair: str
    entry_signals: int
    entry_sides: list[str]
    entry_reasons: list[str]
    opened_orders: int
    rejected_actions: int
    blocked_actions: int
    protection_active: bool
    protection_reasons: list[str]
    open_trade_count: int
    exit_reasons: list[str]


class TimelinePayload(TypedDict):
    surface: str
    step_count: int
    steps: list[TimelineStepPayload]


class BacktestPayload(TypedDict):
    strategy: StrategyPayload
    timeline: TimelinePayload


BACKTEST_PAYLOAD_ADAPTER: Final = TypeAdapter(BacktestPayload)
TIMELINE_PAYLOAD_ADAPTER: Final = TypeAdapter(TimelinePayload)
STRATEGY_INSPECT_PAYLOAD_ADAPTER: Final = TypeAdapter(StrategyInspectPayload)


def test_x7_native_config_is_selectable_by_config_and_strategy_cli() -> None:
    # Given
    validate_command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "validate",
        "--config",
        X7_CONFIG,
    ]
    inspect_command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "strategy",
        "inspect",
        "--config",
        X7_CONFIG,
        "--strategy",
        X7_STRATEGY,
    ]

    # When
    validate_result = subprocess.run(
        validate_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    inspect_result = subprocess.run(
        inspect_command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then
    assert validate_result.returncode == 0, validate_result.stderr
    assert inspect_result.returncode == 0, inspect_result.stderr
    assert "strategy_name=X7NativeStrategy" in inspect_result.stdout
    assert "timeframe=5m" in inspect_result.stdout
    assert "can_short=true" in inspect_result.stdout


def test_x7_native_strategy_inspect_json_reports_semantic_coverage() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "strategy",
        "inspect",
        "--config",
        X7_CONFIG,
        "--strategy",
        X7_STRATEGY,
        "--json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    payload = STRATEGY_INSPECT_PAYLOAD_ADAPTER.validate_json(result.stdout)
    coverage = payload["semantic_coverage"]
    assert payload["strategy_name"] == "X7NativeStrategy"
    assert coverage["is_full_semantic_coverage"] is True
    assert coverage["pending_modules"] == []
    assert "metadata" in coverage["covered_modules"]
    assert "indicator_runtime" in coverage["covered_modules"]
    assert "feature_graph" in coverage["covered_modules"]
    assert "entry_signals" in coverage["covered_modules"]
    assert "exit_signals" in coverage["covered_modules"]
    assert "stake_sizing" in coverage["covered_modules"]
    assert "protections" in coverage["covered_modules"]
    assert "release_docs" in coverage["covered_modules"]
    assert coverage["modules"][0]["status"] == "verified"


def test_x7_native_config_is_selectable_by_backtest_json_surface() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "backtest",
        "--config",
        X7_CONFIG,
        "--json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    payload = BACKTEST_PAYLOAD_ADAPTER.validate_json(result.stdout)
    assert payload["strategy"]["name"] == "X7NativeStrategy"
    assert payload["timeline"]["steps"][0]["pair"] == "BTC/USDT:USDT"
    assert payload["timeline"]["steps"][1]["entry_signals"] == 1
    assert payload["timeline"]["steps"][1]["entry_sides"] == ["long"]
    assert payload["timeline"]["steps"][1]["entry_reasons"] == [LONG_ENTRY_TAG]


def test_x7_native_config_is_selectable_by_paper_run_surface(tmp_path: Path) -> None:
    # Given
    timeline_path = tmp_path / "x7-paper-timeline.json"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "paper-run",
        "--config",
        X7_CONFIG,
        "--ticks",
        "tests/fixtures/ticks/btc_usdt_futures.jsonl",
        "--max-events",
        "5",
        "--timeline-output",
        str(timeline_path),
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "processed_events=5" in result.stdout
    assert "created_trades=3" in result.stdout
    assert "live_orders=false" in result.stdout
    timeline = TIMELINE_PAYLOAD_ADAPTER.validate_json(timeline_path.read_text(encoding="utf-8"))
    assert timeline["surface"] == "paper"
    assert timeline["step_count"] == 5
    assert timeline["steps"][0]["pair"] == "BTC/USDT:USDT"
    assert timeline["steps"][0]["entry_signals"] == 0
    assert timeline["steps"][0]["entry_reasons"] == []
    assert timeline["steps"][1]["entry_signals"] == 1
    assert timeline["steps"][1]["entry_sides"] == ["long"]
    assert timeline["steps"][1]["entry_reasons"] == [LONG_ENTRY_TAG]
    assert timeline["steps"][3]["opened_orders"] == 1
    assert timeline["steps"][3]["open_trade_count"] == 3
    assert timeline["steps"][4]["entry_reasons"] == [LONG_ENTRY_TAG]
    assert timeline["steps"][4]["opened_orders"] == 0
    assert timeline["steps"][4]["rejected_actions"] == 1
    assert timeline["steps"][4]["open_trade_count"] == 3
    assert "signal_side" not in timeline_path.read_text(encoding="utf-8")


def test_x7_native_paper_timeline_records_protection_reasons(tmp_path: Path) -> None:
    # Given
    timeline_path = tmp_path / "x7-paper-protection-timeline.json"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "paper-run",
        "--config",
        X7_CONFIG,
        "--ticks",
        "tests/fixtures/ticks/stale_stream.jsonl",
        "--max-events",
        "3",
        "--timeline-output",
        str(timeline_path),
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "new_orders_blocked=true" in result.stdout
    timeline = TIMELINE_PAYLOAD_ADAPTER.validate_json(timeline_path.read_text(encoding="utf-8"))
    blocked_step = timeline["steps"][2]
    assert blocked_step["entry_signals"] == 1
    assert blocked_step["entry_sides"] == ["long"]
    assert blocked_step["entry_reasons"] == [LONG_ENTRY_TAG]
    assert blocked_step["blocked_actions"] == 1
    assert blocked_step["protection_active"] is True
    assert blocked_step["protection_reasons"] == ["stale_data"]


def test_x7_native_paper_run_blocks_preflight_guardrail_before_strategy_timeline(
    tmp_path: Path,
) -> None:
    # Given
    timeline_path = tmp_path / "x7-blocked-paper-timeline.json"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "paper-run",
        "--config",
        X7_PREFLIGHT_BLOCKED_CONFIG,
        "--ticks",
        "tests/fixtures/ticks/btc_usdt_futures.jsonl",
        "--max-events",
        "5",
        "--timeline-output",
        str(timeline_path),
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 1
    assert "PREFLIGHT_BLOCKED" in result.stderr
    assert "FUTURES_LEVERAGE_INVALID" in result.stderr
    assert "fake-live-api-key" not in result.stderr
    assert timeline_path.exists() is False
