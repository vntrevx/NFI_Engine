from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum, unique
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


@unique
class DataLifecycleCategoryName(StrEnum):
    SQLITE = "sqlite"
    LOGS = "logs"
    BACKUPS = "backups"
    SUPPORT_BUNDLES = "support_bundles"
    EVIDENCE = "evidence"


@unique
class DataLifecycleItemStatus(StrEnum):
    CANDIDATE = "candidate"
    PROTECTED = "protected"
    REMOVED = "removed"
    SKIPPED = "skipped"
    MISSING = "missing"


@dataclass(frozen=True, slots=True)
class DataLifecycleFile:
    category: DataLifecycleCategoryName
    path: str
    size_bytes: int
    modified_at: datetime | None
    status: DataLifecycleItemStatus
    reason: str


@dataclass(frozen=True, slots=True)
class DataLifecycleCategoryFootprint:
    name: DataLifecycleCategoryName
    root: str
    file_count: int
    total_bytes: int
    items: tuple[DataLifecycleFile, ...]


@dataclass(frozen=True, slots=True)
class DataLifecycleFootprint:
    generated_at: datetime
    config_source: str
    total_bytes: int
    categories: tuple[DataLifecycleCategoryFootprint, ...]


@dataclass(frozen=True, slots=True)
class DataLifecycleExport:
    receipt_id: str
    generated_at: datetime
    redacted_config_json: str
    redacted_profile_json: str
    footprint: DataLifecycleFootprint


@dataclass(frozen=True, slots=True)
class DataLifecyclePrunePolicy:
    retention_days: int = 7
    dry_run: bool = True
    apply: bool = False
    preview_token: str | None = None
    confirm_scope: str | None = None


@dataclass(frozen=True, slots=True)
class DataLifecyclePruneReceipt:
    receipt_id: str
    accepted: bool
    dry_run: bool
    apply: bool
    mutation_applied: bool
    retention_days: int
    preview_token: str
    candidate_count: int
    deleted_count: int
    protected_count: int
    skipped_count: int
    bytes_reclaimable: int
    bytes_deleted: int
    blocked_reasons: tuple[str, ...]
    items: tuple[DataLifecycleFile, ...]


class DataLifecycleProfilePayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    engine_version: str
    environment: str
    locale: str
    read_only: bool
    exchange_name: str
    trading_mode: str
    testnet: bool
    strategy_name: str
    strategy_module: str
    config_source: str
    database_url: str
    footprint_total_bytes: int


@dataclass(frozen=True, slots=True)
class DataLifecycleRoots:
    sqlite: Path | None
    runtime: Path
    logs: Path
    backups: Path
    support_bundles: Path
    evidence: Path
