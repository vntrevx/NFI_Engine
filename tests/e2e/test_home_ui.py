from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.config.models import RuntimeSettings
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


@pytest.mark.anyio
async def test_home_route_is_first_usable_operator_surface() -> None:
    async with _client(
        create_app(
            settings=RuntimeSettings(),
            dashboard_store=StaticDashboardReadStore(),
        ),
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert 'data-testid="home-root"' in response.text
    assert 'href="/settings"' in response.text
    assert 'href="/logs"' in response.text
    assert 'data-testid="bot-state"' in response.text
    assert 'data-testid="session-pnl"' in response.text
    assert 'data-testid="open-trades"' in response.text
    assert 'data-testid="runtime-controls"' in response.text
    assert 'data-testid="runtime-control-state"' in response.text
    assert 'data-testid="pause-button"' in response.text
    assert 'data-testid="resume-button"' in response.text
    assert 'data-command="start"' in response.text
    assert 'data-command="pause"' in response.text
    assert 'data-command="resume"' in response.text
    assert 'data-command="stop"' in response.text
    assert 'data-testid="dashboard-chart"' in response.text
    assert 'data-testid="chart-status"' in response.text
    assert 'data-testid="chart-render-time"' in response.text
    assert 'data-testid="action-queue"' in response.text
    assert 'data-testid="action-item"' in response.text
    assert 'data-poll-ms="5000"' in response.text
    assert "/api/v1/dashboard/snapshot" in response.text
    assert "/api/v1/runtime/control" in response.text
    assert "/api/v1/runtime/health" in response.text
    assert "chart-bars" not in response.text
    assert "/api/v1/reports/support-bundle.zip" in response.text
    assert "https://" not in response.text
    assert "cdn" not in response.text.lower()
    assert "localStorage" not in response.text
    assert "sessionStorage" not in response.text


@pytest.mark.anyio
async def test_home_route_renders_bounded_dashboard_read_model_summary() -> None:
    read_store = StaticDashboardReadStore(
        DashboardReadModels(
            equity_points=(
                DashboardEquityPoint(
                    at=datetime(2026, 1, 1, tzinfo=UTC),
                    equity=Decimal("1000.00"),
                    available=Decimal("875.50"),
                ),
            ),
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
    async with _client(
        create_app(settings=RuntimeSettings(), dashboard_store=read_store),
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200
    assert 'data-testid="open-trades"><span>Open trades</span><strong>1</strong>' in response.text
    assert (
        'data-testid="session-pnl"><span>Session PnL</span><strong>12.34 USDT</strong>'
        in response.text
    )
    assert 'data-testid="runtime-control-state">stopped<' in response.text
    assert 'data-testid="portfolio-summary"' in response.text
    assert (
        'data-testid="portfolio-equity"><span>Account equity</span><strong>1000.00 USDT</strong>'
        in response.text
    )
    assert (
        'data-testid="portfolio-exposure"><span>Gross exposure</span><strong>20.00 USDT</strong>'
        in response.text
    )
    assert 'data-testid="portfolio-risk-pressure">Balanced</strong>' in response.text
    assert "profit-placeholder" not in response.text


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
