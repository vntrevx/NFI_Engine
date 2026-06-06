from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from nfi_engine.api.models import initial_log_entries
from nfi_engine.api.routes import build_api_router
from nfi_engine.api.security import SecurityContext
from nfi_engine.api.settings import resolve_runtime_settings, validate_api_auth_settings
from nfi_engine.api.state import ApiContext, ApiRuntimeState
from nfi_engine.api.ui import logs_page, settings_page
from nfi_engine.config import RuntimeSettings
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.preflight.service import run_preflight
from nfi_engine.profiles.catalog import default_profile_name


def create_app(
    settings: RuntimeSettings | None = None,
    config_path: Path | None = None,
) -> FastAPI:
    resolved_settings = settings if settings is not None else resolve_runtime_settings(config_path)
    validate_api_auth_settings(resolved_settings)
    context = ApiContext(settings=resolved_settings, runtime=ApiRuntimeState())
    security = SecurityContext.from_settings(resolved_settings)
    logs = initial_log_entries()
    readiness = _readiness(settings=resolved_settings, config_path=config_path)
    app = FastAPI(title="NFI Engine API", version="0.1.0")
    app.add_api_route(
        "/settings",
        settings_page(resolved_settings, readiness, security),
        methods=["GET"],
        include_in_schema=False,
    )
    app.add_api_route("/logs", logs_page(logs, security), methods=["GET"], include_in_schema=False)
    app.include_router(build_api_router(context, logs=logs, security=security), prefix="/api/v1")
    return app


def _readiness(*, settings: RuntimeSettings, config_path: Path | None) -> PreflightReport:
    return run_preflight(
        settings=settings,
        profile_name=default_profile_name(settings),
        config_path=config_path,
    )
