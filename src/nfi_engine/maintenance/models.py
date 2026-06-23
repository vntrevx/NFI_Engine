from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import override


@unique
class MaintenanceErrorCode(StrEnum):
    BACKUP_INVALID = "BACKUP_INVALID"
    BACKUP_RESTORE_APPLY_UNSUPPORTED = "BACKUP_RESTORE_APPLY_UNSUPPORTED"
    BACKUP_REQUIRED = "BACKUP_REQUIRED"
    CONFIG_VERSION_UNSUPPORTED = "CONFIG_VERSION_UNSUPPORTED"
    DATABASE_NOT_READABLE = "DATABASE_NOT_READABLE"
    UNKNOWN_CONFIG_KEY = "UNKNOWN_CONFIG_KEY"


@dataclass(frozen=True, slots=True)
class MaintenanceError(Exception):
    code: MaintenanceErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


@dataclass(frozen=True, slots=True)
class DatabaseMigrationPlan:
    database: str
    current_version: int
    target_version: int
    apply: bool
    backup_reference: str | None
    steps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConfigMigrationPlan:
    config: str
    current_schema_version: int
    target_schema_version: int
    apply: bool
    backup_reference: str | None
    steps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ConfigHistoryEntry:
    version: str
    schema_version: int
    config_hash: str
    strategy_name: str
    strategy_module: str


@dataclass(frozen=True, slots=True)
class RollbackPlan:
    config: str
    to_version: str
    apply: bool
    backup_reference: str | None
    steps: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BackupResult:
    output: str
    manifest_valid: bool
    redacted: bool
    entries: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BackupVerification:
    archive: str
    manifest_valid: bool
    redacted: bool
    entries: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class BackupRestorePlan:
    archive: str
    apply: bool
    manifest_valid: bool
    entries: tuple[str, ...]
    steps: tuple[str, ...]
