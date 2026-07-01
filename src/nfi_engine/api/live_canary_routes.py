from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import APIRouter
from nfi_engine.api.state import ApiContext
from nfi_engine.exchange.live_canary import build_live_canary_preview
from nfi_engine.exchange.live_canary_models import LiveCanaryPreview


def add_live_canary_routes(read_router: APIRouter, *, context: ApiContext) -> None:
    read_router.add_api_route(
        "/exchange/live-canary/preview",
        _preview(context),
        methods=["GET"],
        response_model=LiveCanaryPreview,
    )


def _preview(context: ApiContext) -> Callable[[], LiveCanaryPreview]:
    def endpoint() -> LiveCanaryPreview:
        return build_live_canary_preview(
            settings=context.settings,
            config_path=context.config_path,
        )

    return endpoint
