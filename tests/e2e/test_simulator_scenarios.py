from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

from nfi_engine.exchange.fill_scenarios import FillSimulationResult

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_simulate_fills_cli_writes_deterministic_scenario_report(tmp_path: Path) -> None:
    # Given: one scenario and two output paths.
    first_output = tmp_path / "fill-a.json"
    second_output = tmp_path / "fill-b.json"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "simulate",
        "fills",
        "--scenario",
        "tests/fixtures/simulator/partial_fill_latency.yaml",
    ]

    # When: the CLI runs twice with the same seed.
    first = subprocess.run(
        [*command, "--output", str(first_output)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    second = subprocess.run(
        [*command, "--output", str(second_output)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then: both runs succeed and produce identical JSON.
    assert first.returncode == 0, first.stderr
    assert second.returncode == 0, second.stderr
    assert first_output.read_text(encoding="utf-8") == second_output.read_text(encoding="utf-8")
    payload = FillSimulationResult.model_validate_json(first_output.read_text(encoding="utf-8"))
    assert payload.scenario_hash != ""
    assert payload.seed == 4242
    assert payload.order_state == "PARTIALLY_FILLED"
    assert "scenario_hash=" in first.stdout


def test_simulate_fills_cli_surfaces_slippage_safety_event(tmp_path: Path) -> None:
    # Given: a slippage spike scenario.
    output = tmp_path / "slippage.json"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "simulate",
        "fills",
        "--scenario",
        "tests/fixtures/simulator/slippage_spike.yaml",
        "--output",
        str(output),
    ]

    # When: the CLI simulates fills.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the JSON and stdout include the safety event.
    assert result.returncode == 0, result.stderr
    payload = FillSimulationResult.model_validate_json(output.read_text(encoding="utf-8"))
    assert payload.circuit_breaker_event is True
    assert "SLIPPAGE_ANOMALY" in payload.events
    assert "SLIPPAGE_ANOMALY" in result.stdout
