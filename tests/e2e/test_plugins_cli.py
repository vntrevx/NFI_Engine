from __future__ import annotations

import subprocess
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


class PluginInspectPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    group: str
    built_in: bool


def test_plugins_list_cli_outputs_required_groups() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "plugins",
        "list",
        "--config",
        "examples/futures-paper.yaml",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    for group_name in ("strategy", "exchange", "risk", "notifier", "data"):
        assert group_name in result.stdout


def test_plugins_inspect_cli_outputs_json_manifest() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "plugins",
        "inspect",
        "--name",
        "simulator-exchange",
        "--group",
        "exchange",
        "--json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    payload = PluginInspectPayload.model_validate_json(result.stdout)

    # Then
    assert result.returncode == 0, result.stderr
    assert payload.name == "simulator-exchange"
    assert payload.group == "exchange"
    assert payload.built_in is True


def test_plugins_list_cli_rejects_duplicate_external_names() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "plugins",
        "list",
        "--config",
        "tests/fixtures/config/duplicate-plugin-root.yaml",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 1
    assert "PLUGIN_DUPLICATE_NAME" in result.stderr
