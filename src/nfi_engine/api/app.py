from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from nfi_engine.api.models import initial_log_entries
from nfi_engine.api.routes import build_api_router
from nfi_engine.api.security import SecurityContext
from nfi_engine.api.settings import (
    resolve_runtime_config_path,
    resolve_runtime_settings,
    validate_api_auth_settings,
)
from nfi_engine.api.state import ApiContext, ApiRuntimeState
from nfi_engine.api.ui import HomePageDependencies, home_page, logs_page, settings_page
from nfi_engine.api.validation_errors import redacted_request_validation_error
from nfi_engine.config import RuntimeSettings
from nfi_engine.dashboard import DashboardReadStore, PersistenceDashboardReadStore
from nfi_engine.persistence import create_persistence_database
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.preflight.service import run_preflight
from nfi_engine.profiles.catalog import default_profile_name
from nfi_engine.wallet import WalletBalanceReader


def create_app(
    settings: RuntimeSettings | None = None,
    config_path: Path | None = None,
    dashboard_store: DashboardReadStore | None = None,
    wallet_balance_reader: WalletBalanceReader | None = None,
) -> FastAPI:
    resolved_config_path = resolve_runtime_config_path(config_path)
    resolved_settings = settings if settings is not None else resolve_runtime_settings(config_path)
    validate_api_auth_settings(resolved_settings)
    context = ApiContext(
        settings=resolved_settings,
        runtime=ApiRuntimeState(),
        dashboard_store=_dashboard_store(resolved_settings, dashboard_store),
        wallet_balance_reader=wallet_balance_reader,
        config_path=resolved_config_path,
    )

    def current_settings() -> RuntimeSettings:
        return context.settings

    security = SecurityContext.from_settings_provider(current_settings)
    logs = initial_log_entries()
    readiness = _readiness(settings=resolved_settings, config_path=resolved_config_path)
    app = FastAPI(title="NFI Engine API", version="0.1.0")
    app.add_exception_handler(RequestValidationError, redacted_request_validation_error)
    app.add_api_route(
        "/",
        home_page(
            current_settings,
            logs,
            readiness,
            security,
            HomePageDependencies(
                dashboard_store=context.dashboard_store,
                runtime_state=context.runtime,
            ),
        ),
        methods=["GET"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/settings",
        settings_page(current_settings, readiness, security),
        methods=["GET"],
        include_in_schema=False,
    )
    app.add_api_route(
        "/logs",
        logs_page(current_settings, logs, security),
        methods=["GET"],
        include_in_schema=False,
    )
    app.include_router(
        build_api_router(context, logs=logs, security=security, readiness=readiness),
        prefix="/api/v1",
    )
    return app


def _readiness(*, settings: RuntimeSettings, config_path: Path | None) -> PreflightReport:
    return run_preflight(
        settings=settings,
        profile_name=default_profile_name(settings),
        config_path=config_path,
    )


def _dashboard_store(
    settings: RuntimeSettings,
    store: DashboardReadStore | None,
) -> DashboardReadStore:
    if store is not None:
        return store
    return PersistenceDashboardReadStore(create_persistence_database(settings.database.url))
