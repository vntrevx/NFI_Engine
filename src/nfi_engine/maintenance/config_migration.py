from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Final

from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.maintenance.models import (
    ConfigHistoryEntry,
    ConfigMigrationPlan,
    MaintenanceError,
    MaintenanceErrorCode,
    RollbackPlan,
)

CONFIG_TARGET_SCHEMA_VERSION: Final = 1
CURRENT_CONFIG_KEYS: Final = frozenset(
    (
        "api",
        "backtest",
        "circuit_breakers",
        "database",
        "engine",
        "exchange",
        "logging",
        "notifications",
        "pairlist",
        "paper_run",
        "plugins",
        "reconciliation",
        "risk",
        "schema_version",
        "strategy",
        "ui",
    ),
)
V0_CONFIG_KEYS: Final = CURRENT_CONFIG_KEYS | frozenset(("paper",))


def build_config_migration_plan(
    *,
    config: Path,
    dry_run: bool,
    backup_reference: str | None = None,
    allow_no_backup_for_dev: bool = False,
) -> ConfigMigrationPlan:
    text = config.read_text(encoding="utf-8")
    top_keys = _top_level_keys(text)
    current_schema_version = _schema_version(text)
    _reject_unknown_keys(top_keys=top_keys, schema_version=current_schema_version)
    apply = not dry_run
    if apply and backup_reference is None and not allow_no_backup_for_dev:
        raise MaintenanceError(
            code=MaintenanceErrorCode.BACKUP_REQUIRED,
            message="config migration apply requires a backup reference",
        )
    plan = ConfigMigrationPlan(
        config=str(config),
        current_schema_version=current_schema_version,
        target_schema_version=CONFIG_TARGET_SCHEMA_VERSION,
        apply=apply,
        backup_reference=backup_reference,
        steps=_config_steps(top_keys=top_keys, schema_version=current_schema_version),
    )
    if apply:
        config.write_text(_migrated_config_text(text), encoding="utf-8")
    return plan


def build_config_history(*, config: Path) -> ConfigHistoryEntry:
    try:
        settings = load_runtime_settings(config)
    except ConfigLoadError as exc:
        raise MaintenanceError(
            code=MaintenanceErrorCode.CONFIG_VERSION_UNSUPPORTED,
            message=str(exc),
        ) from exc
    return ConfigHistoryEntry(
        version="current",
        schema_version=CONFIG_TARGET_SCHEMA_VERSION,
        config_hash=_sha256_file(config),
        strategy_name=settings.strategy.name,
        strategy_module=settings.strategy.module,
    )


def preview_config_rollback(
    *,
    config: Path,
    to_version: str,
    apply: bool,
    backup_reference: str | None,
    allow_no_backup_for_dev: bool = False,
) -> RollbackPlan:
    if apply and backup_reference is None and not allow_no_backup_for_dev:
        raise MaintenanceError(
            code=MaintenanceErrorCode.BACKUP_REQUIRED,
            message="config rollback apply requires a backup reference",
        )
    return RollbackPlan(
        config=str(config),
        to_version=to_version,
        apply=apply,
        backup_reference=backup_reference,
        steps=("load immutable config history", "preview rollback diff", "restore config snapshot"),
    )


def _top_level_keys(text: str) -> frozenset[str]:
    return frozenset(
        key for key in (_top_level_key(line) for line in text.splitlines()) if key is not None
    )


def _top_level_key(line: str) -> str | None:
    stripped = line.strip()
    if stripped == "" or stripped.startswith("#") or line.startswith((" ", "\t")):
        return None
    key, separator, _value = stripped.partition(":")
    if separator == "":
        return None
    return key


def _schema_version(text: str) -> int:
    for line in text.splitlines():
        stripped = line.strip()
        key, separator, value = stripped.partition(":")
        if key == "schema_version" and separator == ":":
            return int(value.strip())
    return CONFIG_TARGET_SCHEMA_VERSION


def _reject_unknown_keys(*, top_keys: frozenset[str], schema_version: int) -> None:
    allowed = V0_CONFIG_KEYS if schema_version == 0 else CURRENT_CONFIG_KEYS
    unknown = tuple(sorted(top_keys - allowed))
    if unknown:
        raise MaintenanceError(
            code=MaintenanceErrorCode.UNKNOWN_CONFIG_KEY,
            message=f"unknown top-level config keys: {','.join(unknown)}",
        )
    if schema_version > CONFIG_TARGET_SCHEMA_VERSION:
        raise MaintenanceError(
            code=MaintenanceErrorCode.CONFIG_VERSION_UNSUPPORTED,
            message=f"schema_version {schema_version} is newer than supported",
        )


def _config_steps(*, top_keys: frozenset[str], schema_version: int) -> tuple[str, ...]:
    if schema_version >= CONFIG_TARGET_SCHEMA_VERSION:
        return ("config schema is current",)
    steps = ["schema_version 0 -> 1"]
    if "paper" in top_keys:
        steps.append("rename paper to paper_run")
    return tuple(steps)


def _migrated_config_text(text: str) -> str:
    lines = tuple(_migrated_config_line(line) for line in text.splitlines())
    return "\n".join(line for line in lines if line != "schema_version: 0") + "\n"


def _migrated_config_line(line: str) -> str:
    if line == "paper:":
        return "paper_run:"
    if line == "schema_version: 0":
        return "schema_version: 1"
    return line


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
