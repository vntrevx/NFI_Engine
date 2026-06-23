from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import ConfigDict, Field

from nfi_engine.api.models import StrictApiModel
from nfi_engine.maintenance.data_lifecycle import (
    DataLifecycleExport,
    DataLifecycleFootprint,
    DataLifecyclePrunePolicy,
    DataLifecyclePruneReceipt,
)
from nfi_engine.maintenance.data_lifecycle_types import (
    DataLifecycleCategoryFootprint,
    DataLifecycleFile,
)


class DataLifecycleFileResponse(StrictApiModel):
    category: str
    path: str
    size_bytes: int
    modified_at: datetime | None
    status: str
    reason: str


class DataLifecycleCategoryFootprintResponse(StrictApiModel):
    name: str
    root: str
    file_count: int
    total_bytes: int
    items: tuple[DataLifecycleFileResponse, ...]


class DataLifecycleFootprintResponse(StrictApiModel):
    generated_at: datetime
    config_source: str
    total_bytes: int
    categories: tuple[DataLifecycleCategoryFootprintResponse, ...]


class DataLifecycleExportResponse(StrictApiModel):
    receipt_id: str
    generated_at: datetime
    redacted_config_json: str
    redacted_profile_json: str
    footprint: DataLifecycleFootprintResponse


class DataLifecyclePruneRequest(StrictApiModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True, strict=True)

    dry_run: bool = True
    apply: bool = False
    retention_days: int = Field(default=7, ge=0, le=3650)
    preview_token: str | None = None
    confirm_scope: str | None = None


class DataLifecyclePruneReceiptResponse(StrictApiModel):
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
    items: tuple[DataLifecycleFileResponse, ...]


def footprint_response(
    footprint: DataLifecycleFootprint,
) -> DataLifecycleFootprintResponse:
    return DataLifecycleFootprintResponse(
        generated_at=footprint.generated_at,
        config_source=footprint.config_source,
        total_bytes=footprint.total_bytes,
        categories=tuple(category_response(category) for category in footprint.categories),
    )


def export_response(export: DataLifecycleExport) -> DataLifecycleExportResponse:
    return DataLifecycleExportResponse(
        receipt_id=export.receipt_id,
        generated_at=export.generated_at,
        redacted_config_json=export.redacted_config_json,
        redacted_profile_json=export.redacted_profile_json,
        footprint=footprint_response(export.footprint),
    )


def prune_policy(request: DataLifecyclePruneRequest) -> DataLifecyclePrunePolicy:
    return DataLifecyclePrunePolicy(
        retention_days=request.retention_days,
        dry_run=request.dry_run,
        apply=request.apply,
        preview_token=request.preview_token,
        confirm_scope=request.confirm_scope,
    )


def prune_receipt_response(
    receipt: DataLifecyclePruneReceipt,
) -> DataLifecyclePruneReceiptResponse:
    return DataLifecyclePruneReceiptResponse(
        receipt_id=receipt.receipt_id,
        accepted=receipt.accepted,
        dry_run=receipt.dry_run,
        apply=receipt.apply,
        mutation_applied=receipt.mutation_applied,
        retention_days=receipt.retention_days,
        preview_token=receipt.preview_token,
        candidate_count=receipt.candidate_count,
        deleted_count=receipt.deleted_count,
        protected_count=receipt.protected_count,
        skipped_count=receipt.skipped_count,
        bytes_reclaimable=receipt.bytes_reclaimable,
        bytes_deleted=receipt.bytes_deleted,
        blocked_reasons=receipt.blocked_reasons,
        items=tuple(file_response(item) for item in receipt.items),
    )


def category_response(
    category: DataLifecycleCategoryFootprint,
) -> DataLifecycleCategoryFootprintResponse:
    return DataLifecycleCategoryFootprintResponse(
        name=category.name.value,
        root=category.root,
        file_count=category.file_count,
        total_bytes=category.total_bytes,
        items=tuple(file_response(item) for item in category.items),
    )


def file_response(item: DataLifecycleFile) -> DataLifecycleFileResponse:
    return DataLifecycleFileResponse(
        category=item.category.value,
        path=item.path,
        size_bytes=item.size_bytes,
        modified_at=item.modified_at,
        status=item.status.value,
        reason=item.reason,
    )
