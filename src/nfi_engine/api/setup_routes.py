from __future__ import annotations

from typing import TYPE_CHECKING

from nfi_engine.api.models import SetupPreviewResponse, config_current_response
from nfi_engine.setup import SetupRequest, build_setup_plan

if TYPE_CHECKING:
    from fastapi import APIRouter


def add_setup_routes(router: APIRouter) -> None:
    router.add_api_route("/setup/preview", _setup_preview, methods=["POST"])


def _setup_preview(request: SetupRequest) -> SetupPreviewResponse:
    plan = build_setup_plan(request)
    return SetupPreviewResponse(
        valid=plan.valid,
        errors=plan.errors,
        redacted_config=None if plan.settings is None else config_current_response(plan.settings),
        config_preview=plan.redacted_config_text,
    )
