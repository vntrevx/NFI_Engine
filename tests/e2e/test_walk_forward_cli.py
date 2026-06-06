from __future__ import annotations

import subprocess
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


class WalkForwardCliPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    splits: list[dict[str, str | int]]
    aggregate_metrics: dict[str, str | int]
    profitability_claim: bool
    metadata: dict[str, str | list[str] | None]


def test_walk_forward_cli_writes_json_output(tmp_path: Path) -> None:
    # Given
    output_path = tmp_path / "walk-forward.json"
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "validate",
        "walk-forward",
        "--config",
        "examples/spot-paper.yaml",
        "--splits",
        "3",
        "--output",
        str(output_path),
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    payload = WalkForwardCliPayload.model_validate_json(output_path.read_text(encoding="utf-8"))

    # Then
    assert result.returncode == 0, result.stderr
    assert len(payload.splits) == 3
    assert payload.aggregate_metrics["total_trades"] == 0
    assert payload.profitability_claim is False
    assert "config_hash" in payload.metadata
    assert "strategy_hash" in payload.metadata
    assert "data_hash" in payload.metadata
    assert "dependency_lock_hash" in payload.metadata


def test_walk_forward_cli_rejects_malformed_split_count() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "validate",
        "walk-forward",
        "--config",
        "examples/spot-paper.yaml",
        "--splits",
        "2",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 1
    assert "WALK_FORWARD_SPLIT_COUNT_INVALID" in result.stderr
