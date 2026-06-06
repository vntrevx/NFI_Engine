from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from nfi_engine.api.state import ApiContext
from nfi_engine.pairlist import (
    PairlistApplyResponse,
    PairlistDraftResponse,
    PairlistPatchRequest,
    PairlistValidationResult,
    preview_pairlist_patch,
)

if TYPE_CHECKING:
    from fastapi import APIRouter


def add_pairlist_routes(
    *,
    read_router: APIRouter,
    write_router: APIRouter,
    context: ApiContext,
) -> None:
    read_router.add_api_route("/pairlist/preview", _preview(context), methods=["POST"])
    write_router.add_api_route("/pairlist/draft", _draft(context), methods=["POST"])
    write_router.add_api_route("/pairlist/apply", _apply(context), methods=["POST"])


def _preview(context: ApiContext) -> Callable[[PairlistPatchRequest], PairlistValidationResult]:
    def endpoint(request: PairlistPatchRequest) -> PairlistValidationResult:
        return preview_pairlist_patch(settings=context.settings, request=request)

    return endpoint


def _draft(context: ApiContext) -> Callable[[PairlistPatchRequest], PairlistDraftResponse]:
    def endpoint(request: PairlistPatchRequest) -> PairlistDraftResponse:
        preview = preview_pairlist_patch(settings=context.settings, request=request)
        return PairlistDraftResponse(
            draft_id="pairlist-draft",
            accepted=True,
            audit_event="PAIRLIST_DRAFT_SAVED",
            preview=preview,
        )

    return endpoint


def _apply(context: ApiContext) -> Callable[[PairlistPatchRequest], PairlistApplyResponse]:
    def endpoint(request: PairlistPatchRequest) -> PairlistApplyResponse:
        preview = preview_pairlist_patch(settings=context.settings, request=request)
        return PairlistApplyResponse(
            applied=True,
            audit_event="PAIRLIST_APPLIED",
            preview=preview,
        )

    return endpoint
