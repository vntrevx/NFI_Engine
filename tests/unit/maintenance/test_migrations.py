from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from nfi_engine.maintenance import (
    MaintenanceError,
    MaintenanceErrorCode,
    build_config_history,
    build_config_migration_plan,
    build_database_migration_plan,
    preview_config_rollback,
    read_database_version,
)


def test_database_dry_run_plan_does_not_mutate_v0_database(tmp_path: Path) -> None:
    # Given: a v0 SQLite fixture copied to an isolated path.
    database = tmp_path / "v0.sqlite"
    shutil.copyfile(Path("tests/fixtures/db/v0.sqlite"), database)

    # When: a dry-run database migration plan is built.
    plan = build_database_migration_plan(database=database, dry_run=True)

    # Then: the plan is explicit and the database user_version is unchanged.
    assert plan.apply is False
    assert plan.current_version == 0
    assert plan.target_version == 1
    assert "create schema_versions table" in plan.steps
    assert read_database_version(database) == 0


def test_database_apply_requires_backup_reference(tmp_path: Path) -> None:
    # Given: a v0 SQLite database and no backup reference.
    database = tmp_path / "v0.sqlite"
    shutil.copyfile(Path("tests/fixtures/db/v0.sqlite"), database)

    # When/Then: mutating migration is blocked by backup guard.
    with pytest.raises(MaintenanceError, match="BACKUP_REQUIRED"):
        build_database_migration_plan(database=database, dry_run=False)


def test_config_migration_dry_run_reports_v0_to_current_schema() -> None:
    # Given: a v0 config fixture.
    config = Path("tests/fixtures/config/v0-config.yaml")

    # When: config migration is previewed.
    plan = build_config_migration_plan(config=config, dry_run=True)

    # Then: schema-version and rename steps are visible without applying.
    assert plan.apply is False
    assert plan.current_schema_version == 0
    assert plan.target_schema_version == 1
    assert "schema_version 0 -> 1" in plan.steps
    assert "rename paper to paper_run" in plan.steps


def test_config_migration_rejects_unknown_top_level_key() -> None:
    # Given: a v0 config fixture with an unknown top-level section.
    config = Path("tests/fixtures/config/v0-config-unknown.yaml")

    # When/Then: migration rejects ambiguous input before planning.
    with pytest.raises(MaintenanceError) as captured:
        build_config_migration_plan(config=config, dry_run=True)
    assert captured.value.code is MaintenanceErrorCode.UNKNOWN_CONFIG_KEY


def test_config_history_reports_current_hash_and_strategy_metadata() -> None:
    # Given: a current fixture config.
    config = Path("examples/futures-paper.yaml")

    # When: config history is built.
    entry = build_config_history(config=config)

    # Then: immutable metadata includes stable hashes and current strategy identity.
    assert entry.version == "current"
    assert len(entry.config_hash) == 64
    assert entry.schema_version == 1
    assert entry.strategy_name == "AdapterSmokeStrategy"


def test_rollback_apply_requires_backup_reference() -> None:
    # Given: a rollback target without backup evidence.
    config = Path("examples/futures-paper.yaml")

    # When/Then: apply is blocked before any config mutation can happen.
    with pytest.raises(MaintenanceError, match="BACKUP_REQUIRED"):
        preview_config_rollback(
            config=config,
            to_version="previous",
            apply=True,
            backup_reference=None,
        )
