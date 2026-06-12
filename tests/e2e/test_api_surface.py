from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.api.dashboard_models import DashboardSnapshotResponse
from nfi_engine.api.models import (
    REDACTED,
    ConfigCurrentResponse,
    ConfigValidationResponse,
    PairHistoryResponse,
    PingResponse,
    ProfitResponse,
    StatusResponse,
    StrategyListResponse,
    TradeListResponse,
)
from nfi_engine.config.models import ApiSettings, RuntimeSettings
from nfi_engine.dashboard.models import (
    DashboardEquityPoint,
    DashboardOpenPosition,
    DashboardReadModels,
    DashboardRecentTrade,
)
from nfi_engine.dashboard.store import StaticDashboardReadStore
from nfi_engine.domain import PositionSide, TradeState

if TYPE_CHECKING:
    from fastapi import FastAPI

LOCAL_BEARER = "local-test-bearer"


@pytest.mark.anyio
async def test_api_surface_exposes_control_and_frontend_routes() -> None:
    # Given: the ASGI app used by uvicorn.
    api_settings = ApiSettings.model_validate({"auth_token": LOCAL_BEARER})
    client = _client(
        create_app(
            settings=RuntimeSettings(api=api_settings),
            dashboard_store=StaticDashboardReadStore(),
        ),
    )
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


@pytest.mark.anyio
async def test_dashboard_snapshot_api_is_protected_and_chart_ready() -> None:
    # Given: a token-protected app with fixture dashboard read models.
    api_settings = ApiSettings.model_validate({"auth_token": LOCAL_BEARER})
    read_store = StaticDashboardReadStore(
        DashboardReadModels(
            equity_points=(
                DashboardEquityPoint(
                    at=datetime(2026, 1, 1, tzinfo=UTC),
                    equity=Decimal("1000.10"),
                    available=Decimal("990.05"),
                ),
            ),
        ),
    )
    client = _client(
        create_app(settings=RuntimeSettings(api=api_settings), dashboard_store=read_store),
    )
    headers = {"Authorization": f"Bearer {LOCAL_BEARER}"}

    # When: unauthenticated and authenticated callers request the snapshot.
    unauthenticated = await client.get("/api/v1/dashboard/snapshot")
    response = await client.get("/api/v1/dashboard/snapshot", headers=headers)
    payload = DashboardSnapshotResponse.model_validate_json(response.content)

    # Then: the route is protected and emits deterministic chart-ready JSON.
    assert unauthenticated.status_code == 401
    assert response.status_code == 200
    assert payload.bot_state == "stopped"
    assert b'"at":"2026-01-01T00:00:00Z"' in response.content
    assert b'"equity":"1000.10"' in response.content
    assert payload.open_positions == ()


@pytest.mark.anyio
async def test_operator_summary_endpoints_use_dashboard_read_models() -> None:
    api_settings = ApiSettings.model_validate({"auth_token": LOCAL_BEARER})
    read_store = StaticDashboardReadStore(
        DashboardReadModels(
            open_positions=(
                DashboardOpenPosition(
                    position_id="position-1",
                    pair="BTC/USDT",
                    side=PositionSide.LONG,
                    quantity=Decimal("0.10"),
                    entry_price=Decimal("100.00"),
                    leverage=Decimal(2),
                    updated_at=datetime(2026, 1, 1, tzinfo=UTC),
                ),
            ),
            recent_trades=(
                DashboardRecentTrade(
                    trade_id="trade-1",
                    pair="BTC/USDT",
                    side=PositionSide.LONG,
                    state=TradeState.CLOSED,
                    opened_at=datetime(2026, 1, 1, tzinfo=UTC),
                    closed_at=datetime(2026, 1, 1, tzinfo=UTC),
                    profit=Decimal("12.34"),
                ),
            ),
        ),
    )
    client = _client(
        create_app(settings=RuntimeSettings(api=api_settings), dashboard_store=read_store),
    )
    headers = {"Authorization": f"Bearer {LOCAL_BEARER}"}

    status_response = await client.get("/api/v1/status", headers=headers)
    profit_response = await client.get("/api/v1/profit", headers=headers)
    trades_response = await client.get("/api/v1/trades", headers=headers)

    assert StatusResponse.model_validate_json(status_response.content).open_trades == 1
    assert ProfitResponse.model_validate_json(profit_response.content).total_profit == Decimal(
        "12.34",
    )
    assert ProfitResponse.model_validate_json(profit_response.content).closed_trades == 1
    assert TradeListResponse.model_validate_json(trades_response.content).items == ("trade-1",)


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
