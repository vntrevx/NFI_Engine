from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from nfi_engine.maintenance.models import (
    DatabaseMigrationPlan,
    MaintenanceError,
    MaintenanceErrorCode,
)

DATABASE_TARGET_VERSION: Final = 1
SQLITE_USER_VERSION_OFFSET: Final = 60
SQLITE_USER_VERSION_LENGTH: Final = 4
SQLITE_HEADER_LENGTH: Final = 100
CREATE_SCHEMA_VERSION_SQL: Final = (
    "CREATE TABLE IF NOT EXISTS schema_versions "
    "(version INTEGER NOT NULL, applied_at TEXT NOT NULL)"
)
DATABASE_MIGRATION_STEPS: Final = (
    "create schema_versions table",
    "record schema version 1",
    "set SQLite user_version 1",
)


def read_database_version(database: Path) -> int:
    try:
        data = database.read_bytes()
    except OSError as exc:
        raise MaintenanceError(
            code=MaintenanceErrorCode.DATABASE_NOT_READABLE,
            message=str(exc),
        ) from exc
    if len(data) < SQLITE_HEADER_LENGTH:
        return 0
    version_bytes = data[
        SQLITE_USER_VERSION_OFFSET : SQLITE_USER_VERSION_OFFSET + SQLITE_USER_VERSION_LENGTH
    ]
    return int.from_bytes(version_bytes, byteorder="big", signed=False)


def build_database_migration_plan(
    *,
    database: Path,
    dry_run: bool,
    backup_reference: str | None = None,
    allow_no_backup_for_dev: bool = False,
) -> DatabaseMigrationPlan:
    current_version = read_database_version(database)
    apply = not dry_run
    if apply and backup_reference is None and not allow_no_backup_for_dev:
        raise MaintenanceError(
            code=MaintenanceErrorCode.BACKUP_REQUIRED,
            message="database migration apply requires a backup reference",
        )
    plan = DatabaseMigrationPlan(
        database=str(database),
        current_version=current_version,
        target_version=DATABASE_TARGET_VERSION,
        apply=apply,
        backup_reference=backup_reference,
        steps=_database_steps(current_version),
    )
    if apply:
        _apply_database_plan(database)
    return plan


def _database_steps(current_version: int) -> tuple[str, ...]:
    if current_version >= DATABASE_TARGET_VERSION:
        return ("database schema is current",)
    return DATABASE_MIGRATION_STEPS


def _apply_database_plan(database: Path) -> None:
    try:
        with sqlite3.connect(database) as connection:
            connection.execute(CREATE_SCHEMA_VERSION_SQL)
            connection.execute(
                "INSERT INTO schema_versions(version, applied_at) VALUES (?, ?)",
                (DATABASE_TARGET_VERSION, datetime.now(UTC).isoformat()),
            )
            connection.execute(f"PRAGMA user_version = {DATABASE_TARGET_VERSION}")
            connection.commit()
    except sqlite3.Error as exc:
        raise MaintenanceError(
            code=MaintenanceErrorCode.DATABASE_NOT_READABLE,
            message=str(exc),
        ) from exc
