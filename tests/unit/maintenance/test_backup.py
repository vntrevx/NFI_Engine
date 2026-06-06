from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from nfi_engine.maintenance import (
    MaintenanceError,
    MaintenanceErrorCode,
    build_database_migration_plan,
    create_backup,
    preview_backup_restore,
    read_database_version,
    verify_backup,
)


def test_backup_create_writes_redacted_manifested_archive(tmp_path: Path) -> None:
    # Given: a config fixture containing exchange secrets.
    output = tmp_path / "backup.zip"

    # When: a backup archive is created.
    result = create_backup(config=Path("tests/fixtures/config/with-secret.yaml"), output=output)

    # Then: required files exist and sensitive values are redacted.
    assert result.output == str(output)
    assert result.manifest_valid is True
    with ZipFile(output) as archive:
        names = set(archive.namelist())
        merged = "\n".join(archive.read(name).decode("utf-8") for name in sorted(names))
        manifest_text = archive.read("manifest.json").decode("utf-8")
    assert {"manifest.json", "config.json", "profile.json", "strategy.json", "logs.json"} <= names
    assert "fixture-secret-value" not in merged
    assert "fixture-key-value" not in merged
    assert "REDACTED" in merged
    assert '"config.json"' in manifest_text


def test_backup_verify_recomputes_manifest_checksums(tmp_path: Path) -> None:
    # Given: a freshly created backup archive.
    output = tmp_path / "backup.zip"
    create_backup(config=Path("examples/futures-paper.yaml"), output=output)

    # When: the archive is verified.
    verification = verify_backup(output)

    # Then: manifest and checksums are valid.
    assert verification.manifest_valid is True
    assert verification.redacted is True
    assert "config.json" in verification.entries


def test_backup_verify_rejects_invalid_archive(tmp_path: Path) -> None:
    # Given: a file that is not a zip archive.
    archive = tmp_path / "not-a-backup.zip"
    archive.write_text("not a backup", encoding="utf-8")

    # When/Then: verification rejects the archive with a typed error.
    with pytest.raises(MaintenanceError) as captured:
        verify_backup(archive)
    assert captured.value.code is MaintenanceErrorCode.BACKUP_INVALID


def test_backup_verify_detects_tampered_member_checksum(tmp_path: Path) -> None:
    # Given: a backup archive whose config member is replaced after manifest creation.
    output = tmp_path / "backup.zip"
    create_backup(config=Path("examples/futures-paper.yaml"), output=output)
    with ZipFile(output) as archive:
        members = tuple(
            (name, b"{}" if name == "config.json" else archive.read(name))
            for name in archive.namelist()
        )
    with ZipFile(output, mode="w", compression=ZIP_DEFLATED) as archive:
        for name, data in members:
            archive.writestr(name, data)

    # When: the archive is verified.
    verification = verify_backup(output)

    # Then: manifest verification fails without trusting the stale manifest.
    assert verification.manifest_valid is False


def test_backup_create_includes_existing_sqlite_database(tmp_path: Path) -> None:
    # Given: a config pointing at an existing SQLite database.
    database = tmp_path / "runtime.sqlite"
    config = tmp_path / "runtime.yaml"
    output = tmp_path / "backup.zip"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE runtime_state(id INTEGER PRIMARY KEY)")
    config.write_text(
        Path("examples/futures-paper.yaml")
        .read_text(encoding="utf-8")
        .replace(
            "sqlite+aiosqlite:///data/nfi_engine.sqlite3",
            f"sqlite+aiosqlite:///{database}",
        ),
        encoding="utf-8",
    )

    # When: a backup archive is created.
    create_backup(config=config, output=output)

    # Then: the SQLite database is included and described in metadata.
    with ZipFile(output) as archive:
        names = set(archive.namelist())
        database_info = archive.read("database.json").decode("utf-8")
    assert "database.sqlite" in names
    assert '"included": true' in database_info


def test_restore_dry_run_reports_plan_without_applying(tmp_path: Path) -> None:
    # Given: a verified backup archive.
    output = tmp_path / "backup.zip"
    create_backup(config=Path("examples/futures-paper.yaml"), output=output)

    # When: restore is previewed.
    plan = preview_backup_restore(archive=output, dry_run=True)

    # Then: restore remains non-mutating and references verified entries.
    assert plan.apply is False
    assert plan.manifest_valid is True
    assert "restore config.json" in plan.steps


def test_restore_apply_requires_verified_backup_reference(tmp_path: Path) -> None:
    # Given: a copied v0 database and a valid backup reference.
    database = tmp_path / "v0.sqlite"
    backup = tmp_path / "backup.zip"
    shutil.copyfile(Path("tests/fixtures/db/v0.sqlite"), database)
    create_backup(config=Path("examples/futures-paper.yaml"), output=backup)

    # When: the backup archive is verified before use.
    verification = verify_backup(backup)
    plan = build_database_migration_plan(
        database=database,
        dry_run=False,
        backup_reference=verification.archive,
    )

    # Then: the verified archive can be used as backup evidence by mutating flows.
    assert verification.manifest_valid is True
    assert plan.apply is True
    assert plan.backup_reference == str(backup)
    assert read_database_version(database) == 1
