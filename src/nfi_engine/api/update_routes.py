from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import TYPE_CHECKING

from nfi_engine.api.state import ApiContext
from nfi_engine.api.update_models import (
    UpdatePreviewResponse,
    UpdateProofReceiptResponse,
    UpdateProofRequest,
    update_preview_response,
    update_proof_receipt_response,
)
from nfi_engine.maintenance.update_provenance import (
    build_update_apply_receipt,
    build_update_preview,
    build_update_rollback_receipt,
)

if TYPE_CHECKING:
    from fastapi import APIRouter


def add_update_routes(
    *,
    read_router: APIRouter,
    write_router: APIRouter,
    context: ApiContext,
) -> None:
    read_router.add_api_route("/update/preview", _preview(context), methods=["GET"])
    write_router.add_api_route("/update/apply", _apply(context), methods=["POST"])
    write_router.add_api_route("/update/rollback", _rollback(context), methods=["POST"])


def _preview(context: ApiContext) -> Callable[[], UpdatePreviewResponse]:
    def endpoint() -> UpdatePreviewResponse:
        preview = build_update_preview(
            settings=context.settings,
            config_path=context.config_path,
            workspace_root=Path.cwd(),
        )
        return update_preview_response(preview)

    return endpoint


def _apply(
    context: ApiContext,
) -> Callable[[UpdateProofRequest | None], UpdateProofReceiptResponse]:
    def endpoint(payload: UpdateProofRequest | None = None) -> UpdateProofReceiptResponse:
        request = payload or UpdateProofRequest()
        preview = build_update_preview(
            settings=context.settings,
            config_path=context.config_path,
            workspace_root=Path.cwd(),
        )
        receipt = build_update_apply_receipt(
            preview=preview,
            policy=request.to_policy(),
        )
        return update_proof_receipt_response(receipt)

    return endpoint


def _rollback(
    context: ApiContext,
) -> Callable[[UpdateProofRequest | None], UpdateProofReceiptResponse]:
    def endpoint(payload: UpdateProofRequest | None = None) -> UpdateProofReceiptResponse:
        request = payload or UpdateProofRequest()
        preview = build_update_preview(
            settings=context.settings,
            config_path=context.config_path,
            workspace_root=Path.cwd(),
        )
        receipt = build_update_rollback_receipt(
            preview=preview,
            policy=request.to_policy(),
        )
        return update_proof_receipt_response(receipt)

    return endpoint
