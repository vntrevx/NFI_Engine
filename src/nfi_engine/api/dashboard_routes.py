from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from nfi_engine.api.dashboard_models import DashboardSnapshotResponse
from nfi_engine.api.models import LogEntryResponse
from nfi_engine.api.state import ApiContext
from nfi_engine.dashboard import build_dashboard_snapshot
from nfi_engine.preflight.models import PreflightReport

if TYPE_CHECKING:
    from fastapi import APIRouter


def add_dashboard_routes(
    router: APIRouter,
    *,
    context: ApiContext,
    logs: tuple[LogEntryResponse, ...],
    readiness: PreflightReport,
) -> None:
    router.add_api_route(
        "/dashboard/snapshot",
        _snapshot(context, logs, readiness),
        methods=["GET"],
    )


def _snapshot(
    context: ApiContext,
    logs: tuple[LogEntryResponse, ...],
    readiness: PreflightReport,
) -> Callable[[], Awaitable[DashboardSnapshotResponse]]:
    async def endpoint() -> DashboardSnapshotResponse:
        read_models = await context.dashboard_store.read_models()
        snapshot = build_dashboard_snapshot(
            settings=context.settings,
            bot_state=context.runtime.state,
            readiness=readiness,
            logs=logs,
            read_models=read_models,
        )
        return DashboardSnapshotResponse.from_snapshot(snapshot)

    return endpoint
