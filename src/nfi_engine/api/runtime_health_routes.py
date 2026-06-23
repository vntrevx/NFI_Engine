from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING

from nfi_engine.api.runtime_health_models import RuntimeHealthResponse
from nfi_engine.api.state import ApiContext
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.runtime_health import RuntimeHealthRequest, build_runtime_health_snapshot
from nfi_engine.wallet import fetch_wallet_balance

if TYPE_CHECKING:
    from fastapi import APIRouter


def add_runtime_health_routes(
    router: APIRouter,
    *,
    context: ApiContext,
    readiness: PreflightReport,
) -> None:
    router.add_api_route("/runtime/health", _runtime_health(context, readiness), methods=["GET"])


def _runtime_health(
    context: ApiContext,
    readiness: PreflightReport,
) -> Callable[[], Awaitable[RuntimeHealthResponse]]:
    async def endpoint() -> RuntimeHealthResponse:
        read_models = await context.dashboard_store.read_models()
        wallet = await fetch_wallet_balance(
            settings=context.settings,
            reader=context.wallet_balance_reader,
        )
        snapshot = build_runtime_health_snapshot(
            RuntimeHealthRequest(
                settings=context.settings,
                bot_state=context.runtime.state,
                readiness=readiness,
                read_models=read_models,
                wallet_balance=wallet,
            ),
        )
        return RuntimeHealthResponse.from_snapshot(snapshot)

    return endpoint
