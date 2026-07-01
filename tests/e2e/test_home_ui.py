from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.api.dashboard_models import DashboardSnapshotResponse
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


def _react_shell(html: str) -> bool:
    return 'id="nfi-react-root"' in html


def _assert_react_shell(html: str) -> None:
    assert 'id="nfi-react-root"' in html
    assert 'data-nfi-page="home"' in html
    assert "/ui-react/assets/" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
    assert "https://" not in html
    assert "cdn" not in html.lower()


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
    if _react_shell(response.text):
        _assert_react_shell(response.text)
        return
    assert 'data-testid="home-root"' in response.text
    assert 'href="/settings"' in response.text
    assert 'href="/logs"' in response.text
    assert 'data-testid="bot-state"' in response.text
    assert 'data-testid="dashboard-primary-stack"' in response.text
    assert 'data-testid="dashboard-ops-rail"' in response.text
    assert 'data-testid="session-pnl"' in response.text
    assert 'data-testid="open-trades"' in response.text
    assert 'data-testid="runtime-controls"' in response.text
    assert 'data-testid="runtime-control-state"' in response.text
    assert 'data-testid="pause-button"' in response.text
    assert 'data-testid="resume-button"' in response.text
    assert 'data-testid="portfolio-summary"' in response.text
    assert 'data-testid="overview-positions"' in response.text
    assert 'data-testid="overview-pnl"' in response.text
    assert 'data-testid="overview-exposure"' in response.text
    assert 'data-testid="overview-equity"' in response.text
    assert 'data-testid="overview-risk"' in response.text
    assert 'data-testid="overview-position-panel"' in response.text
    assert 'data-testid="overview-pnl-panel"' in response.text
    assert 'data-command="start"' in response.text
    assert 'data-command="pause"' in response.text
    assert 'data-command="resume"' in response.text
    assert 'data-command="stop"' in response.text
    assert 'data-testid="dashboard-chart"' in response.text
    assert 'data-testid="chart-status"' in response.text
    assert 'data-testid="chart-render-time"' in response.text
    assert 'data-testid="action-queue"' in response.text
    assert 'data-testid="action-item"' in response.text
    assert 'data-testid="execution-safety-signals"' in response.text
    assert 'data-testid="execution-signal-order_lifecycle"' in response.text
    assert 'data-testid="execution-signal-partial_fill_exposure"' in response.text
    assert 'data-poll-ms="5000"' in response.text
    assert "/api/v1/dashboard/snapshot" in response.text
    assert "/api/v1/runtime/control" in response.text
    assert "/api/v1/runtime/health" in response.text
    assert "chart-bars" not in response.text
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
        if _react_shell(response.text):
            snapshot = await client.get("/api/v1/dashboard/snapshot")
            assert response.status_code == 200
            assert snapshot.status_code == 200
            payload = DashboardSnapshotResponse.model_validate_json(snapshot.text)
            assert payload.open_positions[0].pair == "BTC/USDT"
            assert payload.recent_trades[0].profit == "12.34"
            assert payload.equity_points[0].equity == "1000.00"
            return

    assert response.status_code == 200
    assert 'data-testid="open-trades"><span>Open trades</span><strong>1</strong>' in response.text
    assert (
        'data-testid="session-pnl"><span>Session PnL</span><strong>12.34 USDT</strong>'
        in response.text
    )
    assert 'data-testid="runtime-control-state">stopped<' in response.text
    assert 'data-testid="portfolio-summary"' in response.text
    equity_label = 'data-testid="overview-equity"><span>Account equity</span>'
    exposure_label = 'data-testid="overview-exposure"><span>Exposure</span>'
    risk_label = 'data-testid="overview-risk"><span>Risk pressure</span>'
    equity_field = 'data-dashboard-field="account-equity"'
    equity_marker = f"{equity_label}<strong {equity_field}>1000.00 USDT</strong>"
    exposure_marker = f'{exposure_label}<strong data-dashboard-field="exposure-pct">2.0%</strong>'
    risk_marker = f'{risk_label}<strong data-dashboard-field="risk-pressure">Balanced</strong>'
    assert equity_marker in response.text
    assert exposure_marker in response.text
    assert 'data-testid="overview-position"><strong>BTC/USDT</strong>' in response.text
    assert "long 0.1 @ 100 | 2.0x" in response.text
    assert 'data-testid="overview-trade"><strong>BTC/USDT</strong>' in response.text
    assert "closed | 12.34 USDT" in response.text
    assert risk_marker in response.text
    assert 'data-testid="portfolio-risk-pressure"' in response.text
    assert 'data-dashboard-field="risk-pressure-badge">Balanced</strong>' in response.text
    assert "profit-placeholder" not in response.text


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
