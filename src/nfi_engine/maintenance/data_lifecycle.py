from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final

from nfi_engine import __version__
from nfi_engine.api.models import config_current_response
from nfi_engine.config import RuntimeSettings
from nfi_engine.maintenance.data_lifecycle_paths import (
    build_lifecycle_roots,
    redacted_database_url,
    scan_lifecycle_categories,
)
from nfi_engine.maintenance.data_lifecycle_types import (
    DataLifecycleCategoryName,
    DataLifecycleExport,
    DataLifecycleFile,
    DataLifecycleFootprint,
    DataLifecycleItemStatus,
    DataLifecycleProfilePayload,
    DataLifecyclePrunePolicy,
    DataLifecyclePruneReceipt,
)

EXPORT_RECEIPT_PREFIX: Final = "data-export-"
PRUNE_RECEIPT_PREFIX: Final = "data-prune-"
TOKEN_BYTES: Final = 12
DATA_LIFECYCLE_CONFIRM_SCOPE: Final = "DELETE_GENERATED_LOCAL_ARTIFACTS"
DATA_LIFECYCLE_CONFIRMATION_REQUIRED: Final = "DATA_LIFECYCLE_CONFIRMATION_REQUIRED"

__all__ = [
    "DATA_LIFECYCLE_CONFIRMATION_REQUIRED",
    "DATA_LIFECYCLE_CONFIRM_SCOPE",
    "DataLifecycleExport",
    "DataLifecycleFootprint",
    "DataLifecyclePrunePolicy",
    "DataLifecyclePruneReceipt",
    "build_data_lifecycle_export",
    "build_data_lifecycle_footprint",
    "build_data_lifecycle_prune_receipt",
]


def build_data_lifecycle_footprint(
    *,
    settings: RuntimeSettings,
    config_path: Path | None,
    workspace_root: Path,
) -> DataLifecycleFootprint:
    roots = build_lifecycle_roots(settings=settings, workspace_root=workspace_root)
    categories = scan_lifecycle_categories(roots=roots)
    return DataLifecycleFootprint(
        generated_at=datetime.now(UTC),
        config_source=_config_source(config_path),
        total_bytes=sum(category.total_bytes for category in categories),
        categories=categories,
    )


def build_data_lifecycle_export(
    *,
    settings: RuntimeSettings,
    config_path: Path | None,
    workspace_root: Path,
) -> DataLifecycleExport:
    footprint = build_data_lifecycle_footprint(
        settings=settings,
        config_path=config_path,
        workspace_root=workspace_root,
    )
    redacted_config_json = config_current_response(settings).model_dump_json(indent=2)
    profile_json = DataLifecycleProfilePayload(
        engine_version=__version__,
        environment=settings.engine.environment,
        locale=settings.ui.locale.value,
        read_only=settings.ui.read_only,
        exchange_name=settings.exchange.name,
        trading_mode=settings.exchange.trading_mode.value,
        testnet=settings.exchange.testnet,
        strategy_name=settings.strategy.name,
        strategy_module=settings.strategy.module,
        config_source=footprint.config_source,
        database_url=redacted_database_url(settings.database.url),
        footprint_total_bytes=footprint.total_bytes,
    ).model_dump_json(indent=2)
    return DataLifecycleExport(
        receipt_id=_receipt_id(EXPORT_RECEIPT_PREFIX, redacted_config_json, profile_json),
        generated_at=datetime.now(UTC),
        redacted_config_json=redacted_config_json,
        redacted_profile_json=profile_json,
        footprint=footprint,
    )


def build_data_lifecycle_prune_receipt(
    *,
    settings: RuntimeSettings,
    config_path: Path | None,
    workspace_root: Path,
    policy: DataLifecyclePrunePolicy,
) -> DataLifecyclePruneReceipt:
    footprint = build_data_lifecycle_footprint(
        settings=settings,
        config_path=config_path,
        workspace_root=workspace_root,
    )
    planned = _planned_items(footprint, policy)
    candidates = tuple(item for item in planned if item.status is DataLifecycleItemStatus.CANDIDATE)
    token = _preview_token(policy=policy, items=candidates)
    blocked = _blocked_reasons(policy=policy, expected_token=token)
    removed = (
        ()
        if blocked or policy.dry_run or not policy.apply
        else tuple(_remove_candidate(item) for item in candidates)
    )
    deleted_count = sum(1 for item in removed if item.status is DataLifecycleItemStatus.REMOVED)
    bytes_deleted = sum(item.size_bytes for item in removed)
    return DataLifecyclePruneReceipt(
        receipt_id=_receipt_id(PRUNE_RECEIPT_PREFIX, token, str(datetime.now(UTC).timestamp())),
        accepted=not blocked,
        dry_run=policy.dry_run,
        apply=policy.apply,
        mutation_applied=deleted_count > 0,
        retention_days=policy.retention_days,
        preview_token=token,
        candidate_count=len(candidates),
        deleted_count=deleted_count,
        protected_count=sum(
            1 for item in planned if item.status is DataLifecycleItemStatus.PROTECTED
        ),
        skipped_count=sum(1 for item in planned if item.status is DataLifecycleItemStatus.SKIPPED),
        bytes_reclaimable=sum(item.size_bytes for item in candidates),
        bytes_deleted=bytes_deleted,
        blocked_reasons=blocked,
        items=removed or planned,
    )


def _planned_items(
    footprint: DataLifecycleFootprint,
    policy: DataLifecyclePrunePolicy,
) -> tuple[DataLifecycleFile, ...]:
    cutoff = datetime.now(UTC) - timedelta(days=policy.retention_days)
    return tuple(
        _planned_item(item, cutoff=cutoff)
        for category in footprint.categories
        for item in category.items
    )


def _planned_item(item: DataLifecycleFile, *, cutoff: datetime) -> DataLifecycleFile:
    if item.status is DataLifecycleItemStatus.MISSING:
        return item
    if item.category is DataLifecycleCategoryName.SQLITE:
        return _replace_item(item, status=DataLifecycleItemStatus.PROTECTED, reason="active_sqlite")
    if item.reason == "unsafe_path":
        return item
    if item.modified_at is None or item.modified_at > cutoff:
        return _replace_item(
            item,
            status=DataLifecycleItemStatus.SKIPPED,
            reason="within_retention",
        )
    return _replace_item(item, status=DataLifecycleItemStatus.CANDIDATE, reason="older_than_policy")


def _remove_candidate(item: DataLifecycleFile) -> DataLifecycleFile:
    path = Path(item.path)
    try:
        path.unlink()
    except FileNotFoundError:
        return _replace_item(item, status=DataLifecycleItemStatus.MISSING, reason="already_missing")
    except PermissionError:
        return _replace_item(
            item,
            status=DataLifecycleItemStatus.SKIPPED,
            reason="permission_denied",
        )
    except OSError:
        return _replace_item(item, status=DataLifecycleItemStatus.SKIPPED, reason="remove_failed")
    return _replace_item(item, status=DataLifecycleItemStatus.REMOVED, reason="removed")


def _replace_item(
    item: DataLifecycleFile,
    *,
    status: DataLifecycleItemStatus,
    reason: str,
) -> DataLifecycleFile:
    return DataLifecycleFile(
        category=item.category,
        path=item.path,
        size_bytes=item.size_bytes,
        modified_at=item.modified_at,
        status=status,
        reason=reason,
    )


def _blocked_reasons(
    *,
    policy: DataLifecyclePrunePolicy,
    expected_token: str,
) -> tuple[str, ...]:
    if not policy.apply or policy.dry_run:
        return ()
    reasons: list[str] = []
    if policy.preview_token != expected_token:
        reasons.append("preview_token_required")
    if policy.confirm_scope != DATA_LIFECYCLE_CONFIRM_SCOPE:
        reasons.append(DATA_LIFECYCLE_CONFIRMATION_REQUIRED)
    return tuple(reasons)


def _preview_token(
    *,
    policy: DataLifecyclePrunePolicy,
    items: tuple[DataLifecycleFile, ...],
) -> str:
    digest = hashlib.sha256(str(policy.retention_days).encode())
    for item in items:
        digest.update(item.path.encode())
        digest.update(str(item.size_bytes).encode())
        digest.update((item.modified_at.isoformat() if item.modified_at else "").encode())
    return digest.hexdigest()[:TOKEN_BYTES]


def _receipt_id(prefix: str, *parts: str) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode())
    return f"{prefix}{digest.hexdigest()[:TOKEN_BYTES]}"


def _config_source(config_path: Path | None) -> str:
    if config_path is None:
        return "runtime"
    return str(config_path)
