from __future__ import annotations

from datetime import datetime
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

CONFIG_NAME: Final = "config.json"
DATABASE_INFO_NAME: Final = "database.json"
DATABASE_NAME: Final = "database.sqlite"
DOCKER_NAME: Final = "docker.json"
LOGS_NAME: Final = "logs.json"
MANIFEST_NAME: Final = "manifest.json"
PROFILE_NAME: Final = "profile.json"
STRATEGY_NAME: Final = "strategy.json"
EXPECTED_BACKUP_MEMBERS: Final[frozenset[str]] = frozenset(
    {
        CONFIG_NAME,
        DATABASE_INFO_NAME,
        DATABASE_NAME,
        DOCKER_NAME,
        LOGS_NAME,
        MANIFEST_NAME,
        PROFILE_NAME,
        STRATEGY_NAME,
    },
)
REQUIRED_BACKUP_MEMBERS: Final[frozenset[str]] = frozenset(
    {
        CONFIG_NAME,
        DATABASE_INFO_NAME,
        DOCKER_NAME,
        LOGS_NAME,
        MANIFEST_NAME,
        PROFILE_NAME,
        STRATEGY_NAME,
    },
)


class StrictBackupModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


class BackupManifestPayload(StrictBackupModel):
    engine_version: str
    generated_at: datetime
    redacted: bool
    config_hash: str
    dependency_lock_hash: str
    files: tuple[str, ...]
    checksums: dict[str, str]


class ProfilePayload(StrictBackupModel):
    name: str
    description: str
    read_only: bool


class StrategyPayload(StrictBackupModel):
    name: str
    module: str
    config_hash: str
    dependency_lock_hash: str


class DatabasePayload(StrictBackupModel):
    database_url: str
    included: bool
    archive_name: str | None


class DockerPayload(StrictBackupModel):
    compose_present: bool
    dockerfile_present: bool


def validate_backup_archive_names(
    *,
    names: tuple[str, ...],
    manifest: BackupManifestPayload,
) -> None:
    archive_names = set(names)
    if len(archive_names) != len(names):
        message = "backup archive contains duplicate members"
        raise ValueError(message)
    manifest_files = set(manifest.files)
    checksum_names = set(manifest.checksums)
    if manifest_files != checksum_names:
        message = "backup manifest files do not match checksums"
        raise ValueError(message)
    if archive_names != (manifest_files | {MANIFEST_NAME}):
        message = "backup archive members do not match manifest"
        raise ValueError(message)
    unsupported_names = archive_names - EXPECTED_BACKUP_MEMBERS
    if unsupported_names:
        joined = ",".join(sorted(unsupported_names))
        message = f"backup archive contains unsupported members: {joined}"
        raise ValueError(message)
    missing_names = REQUIRED_BACKUP_MEMBERS - archive_names
    if missing_names:
        joined = ",".join(sorted(missing_names))
        message = f"backup archive is missing required members: {joined}"
        raise ValueError(message)
