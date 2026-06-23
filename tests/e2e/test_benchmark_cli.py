from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_benchmark_m2_command_writes_valid_json_report(tmp_path: Path) -> None:
    # Given: an output path for the M2 local benchmark report.
    output = tmp_path / "m2-benchmark.json"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "benchmark",
        "m2",
        "--output",
        str(output),
        "--samples",
        "2",
    ]

    # When: the benchmark command runs.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    pretty = subprocess.run(
        [sys.executable, "-m", "json.tool", str(output)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    content = output.read_text(encoding="utf-8") if output.exists() else ""

    # Then: it writes a JSON report with NFI-only baselines and optional comparison fields.
    assert result.returncode == 0, result.stderr
    assert pretty.returncode == 0, pretty.stderr
    assert '"benchmark": "m2"' in content
    assert '"dashboard_snapshot_latency"' in content
    assert '"home_render_smoke"' in content
    assert '"chart_render_smoke"' in content
    assert '"backtest_720_candle_latency"' in content
    assert '"x7_strategy_inspect_latency"' in content
    assert '"x7_feature_graph_latency"' in content
    assert '"x7_backtest_sample_latency"' in content
    assert '"x7_paper_sample_latency"' in content
    assert '"startup_smoke"' in content
    assert '"install_smoke"' in content
    assert '"freqtrade_available": false' in content
    assert '"claim_allowed": false' in content


def test_benchmark_m2_command_fails_unapproved_regression(tmp_path: Path) -> None:
    # Given: a baseline that is unrealistically faster than the current local run.
    output = tmp_path / "m2-benchmark.json"
    baseline = tmp_path / "baseline.json"
    baseline.write_text(
        """{
  "schema_version": 1,
  "benchmark": "m2",
  "generated_at": "2026-01-01T00:00:00Z",
  "environment": {
    "python": "baseline",
    "platform": "baseline",
    "machine": "baseline",
    "processor": "baseline",
    "cpu_count": 1
  },
  "regression_budget_percent": 5.0,
  "allow_regression": false,
  "regression_reason": null,
  "measurements": [
    {
      "name": "dashboard_snapshot_latency",
      "workflow": "baseline",
      "samples": 1,
      "duration_ms": 0.001,
      "budget_ms": 50.0,
      "status": "pass",
      "data_label": "fixture-empty"
    }
  ],
  "freqtrade_comparison": {
    "freqtrade_available": false,
    "freqtrade_version": null,
    "workflow": "not-run",
    "nfi_engine_result": null,
    "freqtrade_result": null,
    "ratio": null,
    "claim_allowed": false
  }
}
""",
        encoding="utf-8",
    )
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "benchmark",
        "m2",
        "--output",
        str(output),
        "--baseline",
        str(baseline),
        "--samples",
        "1",
    ]

    # When: the benchmark is compared without an explicit regression override.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: it fails with a typed performance regression code.
    assert result.returncode == 1
    assert "PERFORMANCE_REGRESSION" in result.stderr


def test_benchmark_m2_shell_script_targets_default_evidence_path() -> None:
    # Given: the M2 benchmark shell wrapper.
    script = (PROJECT_ROOT / "scripts" / "benchmark_m2.sh").read_text(encoding="utf-8")

    # When/Then: it writes the canonical M2 evidence file through the CLI.
    assert "uv run nfi-engine benchmark m2" in script
    assert ".omo/evidence/m2-benchmark.json" in script
    assert "python3 -m json.tool .omo/evidence/m2-benchmark.json" in script
