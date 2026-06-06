from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_db_migrate_dry_run_cli_reports_plan() -> None:
    # Given: the migration CLI and a v0 SQLite fixture.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "db",
        "migrate",
        "--dry-run",
        "--database",
        "tests/fixtures/db/v0.sqlite",
    ]

    # When: the dry-run migration command executes.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the plan is printed without mutating the fixture.
    assert result.returncode == 0, result.stderr
    assert "migration_plan=database" in result.stdout
    assert "apply=false" in result.stdout
    assert "current_version=0" in result.stdout
    assert "target_version=1" in result.stdout


def test_config_migrate_dry_run_cli_reports_schema_change() -> None:
    # Given: the config migration CLI and a v0 config fixture.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "migrate",
        "--dry-run",
        "--config",
        "tests/fixtures/config/v0-config.yaml",
    ]

    # When: the dry-run config migration command executes.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: schema migration steps are visible.
    assert result.returncode == 0, result.stderr
    assert "migration_plan=config" in result.stdout
    assert "apply=false" in result.stdout
    assert "schema_version 0 -> 1" in result.stdout


def test_config_history_cli_reports_current_hash() -> None:
    # Given: the config history CLI and current futures fixture.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "history",
        "--config",
        "examples/futures-paper.yaml",
    ]

    # When: history is requested.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: immutable metadata is printed.
    assert result.returncode == 0, result.stderr
    assert "version=current" in result.stdout
    assert "config_hash=" in result.stdout
    assert "schema_version=1" in result.stdout


def test_config_rollback_cli_requires_backup() -> None:
    # Given: a rollback apply request without backup reference.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "rollback",
        "--to-version",
        "previous",
        "--config",
        "examples/futures-paper.yaml",
    ]

    # When: rollback is requested.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the backup guard blocks mutation.
    assert result.returncode == 1
    assert "BACKUP_REQUIRED" in result.stderr
