from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from nfi_engine.api.config_edit import check_config_patch
from nfi_engine.api.models import (
    ConfigApplyResponse,
    ConfigCurrentResponse,
    ConfigDraftResponse,
    ConfigMutationRequest,
    ConfigSchemaResponse,
    ConfigValidationResponse,
    config_current_response,
    config_schema_response,
)
from nfi_engine.api.state import ApiContext
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.preflight.service import run_preflight
from nfi_engine.profiles.catalog import default_profile_name

if TYPE_CHECKING:
    from fastapi import APIRouter


def add_config_routes(
    *,
    read_router: APIRouter,
    write_router: APIRouter,
    context: ApiContext,
) -> None:
    read_router.add_api_route("/config/current", _config_current(context), methods=["GET"])
    read_router.add_api_route("/config/schema", _config_schema, methods=["GET"])
    read_router.add_api_route("/preflight", _preflight(context), methods=["GET"])
    read_router.add_api_route("/config/validate", _config_validate, methods=["POST"])
    write_router.add_api_route("/reload_config", _config_validate, methods=["POST"])
    write_router.add_api_route("/config/draft", _config_draft, methods=["POST"])
    write_router.add_api_route("/config/apply", _config_apply, methods=["POST"])


def _config_current(context: ApiContext) -> Callable[[], ConfigCurrentResponse]:
    def endpoint() -> ConfigCurrentResponse:
        return config_current_response(context.settings)

    return endpoint


def _config_schema() -> ConfigSchemaResponse:
    return config_schema_response()


def _preflight(context: ApiContext) -> Callable[[], PreflightReport]:
    def endpoint() -> PreflightReport:
        return run_preflight(
            settings=context.settings,
            profile_name=default_profile_name(context.settings),
        )

    return endpoint


def _config_draft(request: ConfigMutationRequest | None = None) -> ConfigDraftResponse:
    fields = () if request is None else request.fields
    check = check_config_patch(fields)
    return ConfigDraftResponse(draft_id="local-draft", accepted=check.valid)


def _config_validate(request: ConfigMutationRequest | None = None) -> ConfigValidationResponse:
    fields = () if request is None else request.fields
    check = check_config_patch(fields)
    return ConfigValidationResponse(valid=check.valid, errors=check.errors)


def _config_apply(request: ConfigMutationRequest | None = None) -> ConfigApplyResponse:
    fields = () if request is None else request.fields
    check = check_config_patch(fields)
    return ConfigApplyResponse(applied=check.valid, restart_required=check.restart_required)
