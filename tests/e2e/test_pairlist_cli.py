from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_pairlist_validate_cli_writes_report() -> None:
    # Given: the futures paper config and a target evidence file.
    output = PROJECT_ROOT / ".omo/evidence/task-27-cli-pairlist.json"
    output.unlink(missing_ok=True)
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "pairlist",
        "validate",
        "--config",
        "examples/futures-paper.yaml",
        "--output",
        str(output),
    ]

    # When: pairlist validation runs through the CLI.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the JSON report contains accepted and rejected pairs.
    assert result.returncode == 0, result.stderr
    assert output.exists()
    report = output.read_text(encoding="utf-8")
    assert "pairlist_validated=true" in result.stdout
    assert '"accepted_pairs"' in report
    assert '"rejected_pairs"' in report
    assert "FUTURES_NOT_SUPPORTED" in report
