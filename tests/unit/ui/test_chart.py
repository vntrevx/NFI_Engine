from __future__ import annotations

from nfi_engine.ui.assets_dashboard import DASHBOARD_SCRIPT
from nfi_engine.ui.chart import render_dashboard_chart_panel


def test_dashboard_chart_panel_renders_canvas_without_external_assets() -> None:
    # Given: a futures operator home dashboard.
    html = render_dashboard_chart_panel(exchange="bybit", trading_mode="futures")

    # When: the chart shell is rendered.
    # Then: the UI exposes a local canvas chart target and no copied/external chart chrome.
    assert 'data-testid="home-chart-shell"' in html
    assert 'data-testid="dashboard-chart"' in html
    assert 'data-testid="chart-status"' in html
    assert 'data-testid="chart-refresh-rate"' in html
    assert "Waiting for dashboard snapshot data." in html
    assert "<svg" not in html.lower()
    assert "https://" not in html
    assert "cdn" not in html.lower()


def test_dashboard_script_polls_snapshot_and_tracks_chart_states() -> None:
    # Given: the local dashboard script.
    script = DASHBOARD_SCRIPT

    # When: the script is served with the home page.
    # Then: it polls the protected snapshot endpoint and handles expected chart states locally.
    assert "/api/v1/dashboard/snapshot" in script
    assert "setInterval" in script
    assert "requestAnimationFrame" in script
    assert "credentials: 'same-origin'" in script
    assert "getContext('2d')" in script
    assert "updateOverview" in script
    assert "data-dashboard-field" in script
    assert "renderedPoints" in script
    assert "chartNonblank" in script
    assert "Authorization" not in script
    assert "loading" in script
    assert "empty" in script
    assert "stale" in script
    assert "error" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "https://" not in script
