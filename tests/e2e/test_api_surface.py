from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.api.models import (
    REDACTED,
    ConfigCurrentResponse,
    ConfigValidationResponse,
    PairHistoryResponse,
    PingResponse,
    StatusResponse,
    StrategyListResponse,
)
from nfi_engine.config.models import ApiSettings, RuntimeSettings

if TYPE_CHECKING:
    from fastapi import FastAPI

LOCAL_BEARER = "local-test-bearer"


@pytest.mark.anyio
async def test_api_surface_exposes_control_and_frontend_routes() -> None:
    # Given: the ASGI app used by uvicorn.
    api_settings = ApiSettings.model_validate({"auth_token": LOCAL_BEARER})
    client = _client(create_app(settings=RuntimeSettings(api=api_settings)))
    headers = {"Authorization": f"Bearer {LOCAL_BEARER}"}

    # When: the operator touches representative REST categories.
    ping = await client.get("/api/v1/ping")
    status = await client.get("/api/v1/status", headers=headers)
    strategies = await client.get("/api/v1/strategies", headers=headers)
    config_current = await client.get("/api/v1/config/current", headers=headers)
    validation = await client.post("/api/v1/config/validate", headers=headers, json={})
    pair_history = await client.get("/api/v1/pair_history?pair=BTC/USDT", headers=headers)

    # Then: each category returns the typed API contract.
    assert PingResponse.model_validate_json(ping.content).status == "pong"
    assert StatusResponse.model_validate_json(status.content).live_orders is False
    assert StrategyListResponse.model_validate_json(strategies.content).items[0].name == (
        "AdapterSmokeStrategy"
    )
    assert ConfigCurrentResponse.model_validate_json(config_current.content).api.auth_token == (
        REDACTED
    )
    assert ConfigValidationResponse.model_validate_json(validation.content).valid is True
    assert PairHistoryResponse.model_validate_json(pair_history.content).pair == "BTC/USDT"


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
