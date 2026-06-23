from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit, urlunsplit
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

from nfi_engine import __version__
from nfi_engine.api.models import LogListResponse, config_current_response, initial_log_entries
from nfi_engine.config import RuntimeSettings, load_runtime_settings
from nfi_engine.events import REDACTED_TEXT
from nfi_engine.maintenance.config_migration import build_config_history
from nfi_engine.maintenance.models import (
    BackupRestorePlan,
    BackupResult,
    BackupVerification,
    MaintenanceError,
    MaintenanceErrorCode,
)
from nfi_engine.profiles import default_profile_name, get_operator_profile

from .backup_manifest import (
    CONFIG_NAME,
    DATABASE_INFO_NAME,
    DATABASE_NAME,
    DOCKER_NAME,
    LOGS_NAME,
    MANIFEST_NAME,
    PROFILE_NAME,
    STRATEGY_NAME,
    BackupManifestPayload,
    DatabasePayload,
    DockerPayload,
    ProfilePayload,
    StrategyPayload,
    validate_backup_archive_names,
)

SQLITE_PREFIX: Final = "sqlite+aiosqlite:///"


@dataclass(frozen=True, slots=True)
class ArchiveMember:
    name: str
    data: bytes


@dataclass(frozen=True, slots=True)
class DatabaseMembers:
    info: ArchiveMember
    data: ArchiveMember | None


def create_backup(*, config: Path, output: Path) -> BackupResult:
    settings = load_runtime_settings(config)
    members = _backup_members(settings=settings, config=config)
    manifest = _manifest_member(members=members, config=config)
    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr(manifest.name, manifest.data)
        for member in members:
            archive.writestr(member.name, member.data)
    verification = verify_backup(output)
    return BackupResult(
        output=str(output),
        manifest_valid=verification.manifest_valid,
        redacted=verification.redacted,
        entries=verification.entries,
    )


def verify_backup(archive: Path) -> BackupVerification:
    try:
        with ZipFile(archive) as opened:
            names = tuple(sorted(opened.namelist()))
            manifest = BackupManifestPayload.model_validate_json(opened.read(MANIFEST_NAME))
            validate_backup_archive_names(names=names, manifest=manifest)
            manifest_valid = _checksums_match(archive=opened, manifest=manifest)
    except (BadZipFile, KeyError, ValueError) as exc:
        raise MaintenanceError(
            code=MaintenanceErrorCode.BACKUP_INVALID,
            message=str(exc),
        ) from exc
    return BackupVerification(
        archive=str(archive),
        manifest_valid=manifest_valid,
        redacted=manifest.redacted,
        entries=names,
    )


def preview_backup_restore(*, archive: Path, dry_run: bool) -> BackupRestorePlan:
    if not dry_run:
        raise MaintenanceError(
            code=MaintenanceErrorCode.BACKUP_RESTORE_APPLY_UNSUPPORTED,
            message="mutating restore apply is not implemented; run restore with --dry-run",
        )
    verification = verify_backup(archive)
    if not verification.manifest_valid:
        raise MaintenanceError(
            code=MaintenanceErrorCode.BACKUP_INVALID,
            message="backup archive manifest checksum verification failed",
        )
    return BackupRestorePlan(
        archive=str(archive),
        apply=False,
        manifest_valid=verification.manifest_valid,
        entries=verification.entries,
        steps=tuple(f"restore {entry}" for entry in verification.entries if entry != MANIFEST_NAME),
    )


def _backup_members(*, settings: RuntimeSettings, config: Path) -> tuple[ArchiveMember, ...]:
    profile = get_operator_profile(default_profile_name(settings))
    history = build_config_history(config=config)
    dependency_lock_hash = _optional_hash(Path("uv.lock"))
    members = [
        ArchiveMember(
            CONFIG_NAME,
            config_current_response(settings).model_dump_json(indent=2).encode(),
        ),
        ArchiveMember(
            LOGS_NAME,
            LogListResponse(items=initial_log_entries()).model_dump_json(indent=2).encode(),
        ),
        ArchiveMember(
            PROFILE_NAME,
            ProfilePayload(
                name=profile.name,
                description=profile.description,
                read_only=profile.read_only,
            )
            .model_dump_json(indent=2)
            .encode(),
        ),
        ArchiveMember(
            STRATEGY_NAME,
            StrategyPayload(
                name=settings.strategy.name,
                module=settings.strategy.module,
                config_hash=history.config_hash,
                dependency_lock_hash=dependency_lock_hash,
            )
            .model_dump_json(indent=2)
            .encode(),
        ),
        ArchiveMember(
            DOCKER_NAME,
            DockerPayload(
                compose_present=Path("compose.yaml").exists(),
                dockerfile_present=Path("Dockerfile").exists(),
            )
            .model_dump_json(indent=2)
            .encode(),
        ),
    ]
    database_member = _database_member(settings)
    members.append(database_member.info)
    if database_member.data is not None:
        members.append(database_member.data)
    return tuple(members)


def _manifest_member(*, members: tuple[ArchiveMember, ...], config: Path) -> ArchiveMember:
    manifest = BackupManifestPayload(
        engine_version=__version__,
        generated_at=datetime.now(UTC),
        redacted=True,
        config_hash=_sha256_file(config),
        dependency_lock_hash=_optional_hash(Path("uv.lock")),
        files=tuple(member.name for member in members),
        checksums={member.name: _sha256_bytes(member.data) for member in members},
    )
    return ArchiveMember(MANIFEST_NAME, manifest.model_dump_json(indent=2).encode())


def _database_member(settings: RuntimeSettings) -> DatabaseMembers:
    path = _sqlite_path(settings.database.url)
    included = path is not None and path.exists()
    info = DatabasePayload(
        database_url=_redacted_database_url(settings.database.url),
        included=included,
        archive_name=DATABASE_NAME if included else None,
    )
    data = (
        None
        if path is None or not path.exists()
        else ArchiveMember(DATABASE_NAME, path.read_bytes())
    )
    info_member = ArchiveMember(DATABASE_INFO_NAME, info.model_dump_json(indent=2).encode())
    return DatabaseMembers(info=info_member, data=data)


def _redacted_database_url(database_url: str) -> str:
    if database_url.startswith(SQLITE_PREFIX):
        return database_url
    parsed = urlsplit(database_url)
    if parsed.scheme == "":
        return database_url
    netloc = parsed.netloc
    if "@" in netloc:
        _, host = netloc.rsplit("@", maxsplit=1)
        netloc = f"{REDACTED_TEXT}@{host}"
    query = REDACTED_TEXT if parsed.query else ""
    if parsed.netloc == "" and database_url.startswith(f"{parsed.scheme}:///"):
        suffix = f"?{query}" if query else ""
        return f"{parsed.scheme}://{parsed.path}{suffix}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, query, ""))


def _sqlite_path(database_url: str) -> Path | None:
    if not database_url.startswith(SQLITE_PREFIX):
        return None
    path_text = database_url.removeprefix(SQLITE_PREFIX)
    if path_text in {"", ":memory:"}:
        return None
    return Path(path_text)


def _checksums_match(*, archive: ZipFile, manifest: BackupManifestPayload) -> bool:
    names = set(archive.namelist())
    for name, expected in manifest.checksums.items():
        if name not in names or _sha256_bytes(archive.read(name)) != expected:
            return False
    return True


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _optional_hash(path: Path) -> str:
    if not path.exists():
        return ""
    return _sha256_file(path)


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
