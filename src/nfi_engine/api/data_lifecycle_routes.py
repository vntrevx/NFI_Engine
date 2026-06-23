from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from nfi_engine.api.data_lifecycle_models import (
    DataLifecycleExportResponse,
    DataLifecycleFootprintResponse,
    DataLifecyclePruneReceiptResponse,
    DataLifecyclePruneRequest,
    export_response,
    footprint_response,
    prune_policy,
    prune_receipt_response,
)
from nfi_engine.api.state import ApiContext
from nfi_engine.maintenance.data_lifecycle import (
    build_data_lifecycle_export,
    build_data_lifecycle_footprint,
    build_data_lifecycle_prune_receipt,
)

if TYPE_CHECKING:
    from fastapi import APIRouter


def add_data_lifecycle_routes(
    *,
    read_router: APIRouter,
    write_router: APIRouter,
    context: ApiContext,
) -> None:
    read_router.add_api_route("/data-lifecycle/footprint", _footprint(context), methods=["GET"])
    read_router.add_api_route("/data-lifecycle/export", _export(context), methods=["GET"])
    write_router.add_api_route("/data-lifecycle/prune", _prune(context), methods=["POST"])


def _footprint(context: ApiContext) -> Callable[[], DataLifecycleFootprintResponse]:
    def endpoint() -> DataLifecycleFootprintResponse:
        footprint = build_data_lifecycle_footprint(
            settings=context.settings,
            config_path=context.config_path,
            workspace_root=Path.cwd(),
        )
        return footprint_response(footprint)

    return endpoint


def _export(context: ApiContext) -> Callable[[], DataLifecycleExportResponse]:
    def endpoint() -> DataLifecycleExportResponse:
        export = build_data_lifecycle_export(
            settings=context.settings,
            config_path=context.config_path,
            workspace_root=Path.cwd(),
        )
        return export_response(export)

    return endpoint


def _prune(
    context: ApiContext,
) -> Callable[[DataLifecyclePruneRequest | None], DataLifecyclePruneReceiptResponse]:
    def endpoint(
        payload: DataLifecyclePruneRequest | None = None,
    ) -> DataLifecyclePruneReceiptResponse:
        request = payload or DataLifecyclePruneRequest()
        receipt = build_data_lifecycle_prune_receipt(
            settings=context.settings,
            config_path=context.config_path,
            workspace_root=Path.cwd(),
            policy=prune_policy(request),
        )
        return prune_receipt_response(receipt)

    return endpoint
