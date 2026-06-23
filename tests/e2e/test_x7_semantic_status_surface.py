from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Final, TypedDict

import pytest
from httpx import ASGITransport, AsyncClient
from pydantic import TypeAdapter

from nfi_engine.api.app import create_app
from nfi_engine.api.runtime_health_models import RuntimeHealthResponse
from nfi_engine.config.loader import load_runtime_settings
from nfi_engine.dashboard.store import StaticDashboardReadStore

if TYPE_CHECKING:
    from fastapi import FastAPI

pytestmark = pytest.mark.anyio

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
X7_CONFIG: Final = "examples/x7-futures-paper.yaml"
X7_STRATEGY: Final = "nfi_engine.strategy.nfi_x7:X7NativeStrategy"


class X7SemanticStatusPayload(TypedDict):
    enabled: bool
    coverage_state: str
    observed_upstream_version: str
    latest_signal_reason: str
    warmup_state: str
    missing_data_state: str
    live_readiness: str
    blocked_reason: str | None


class StrategyInspectPayload(TypedDict):
    strategy_name: str
    x7_semantic_status: X7SemanticStatusPayload | None


STRATEGY_INSPECT_ADAPTER: Final = TypeAdapter(StrategyInspectPayload)


def test_x7_strategy_inspect_json_reports_operator_semantic_status() -> None:
    # Given: the native X7 strategy inspect surface.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "strategy",
        "inspect",
        "--config",
        X7_CONFIG,
        "--strategy",
        X7_STRATEGY,
        "--json",
    ]

    # When: the operator requests machine-readable inspection.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: the payload exposes evidence-bound status without claiming live readiness.
    assert result.returncode == 0, result.stderr
    payload = STRATEGY_INSPECT_ADAPTER.validate_json(result.stdout)
    status = payload["x7_semantic_status"]
    assert status is not None
    assert status["enabled"] is True
    assert status["observed_upstream_version"] == "v17.4.258"
    assert status["coverage_state"] == "verified"
    assert status["latest_signal_reason"] == "no_runtime_signal_observed"
    assert status["warmup_state"] == "not_observed"
    assert status["missing_data_state"] == "no_dashboard_data"
    assert status["live_readiness"] == "gated"


async def test_runtime_health_api_includes_x7_semantic_status() -> None:
    # Given: the X7 paper/testnet app with no dashboard history yet.
    settings = load_runtime_settings(PROJECT_ROOT / X7_CONFIG)
    async with _client(
        create_app(settings=settings, dashboard_store=StaticDashboardReadStore()),
    ) as client:
        # When: the operator reads runtime health.
        response = await client.get("/api/v1/runtime/health")

    # Then: the API includes X7 semantic status and degraded data wording.
    payload = RuntimeHealthResponse.model_validate_json(response.content)
    assert response.status_code == 200
    assert payload.x7_semantic_status.enabled is True
    assert payload.x7_semantic_status.observed_upstream_version == "v17.4.258"
    assert payload.x7_semantic_status.latest_signal_reason == "no_runtime_signal_observed"
    assert payload.x7_semantic_status.missing_data_state == "no_dashboard_data"
    assert payload.x7_semantic_status.live_readiness == "gated"
    assert "live_ready" not in response.text


async def test_home_ui_renders_x7_semantic_status_without_live_ready_claim() -> None:
    # Given: the X7 operator Home surface.
    settings = load_runtime_settings(PROJECT_ROOT / X7_CONFIG)
    async with _client(
        create_app(settings=settings, dashboard_store=StaticDashboardReadStore()),
    ) as client:
        # When: Home is rendered.
        response = await client.get("/")

    # Then: the local UI shows status, provenance, and blocked/gated wording.
    assert response.status_code == 200
    assert 'data-testid="x7-semantic-status"' in response.text
    assert "NFI X7 semantic status" in response.text
    assert "v17.4.258" in response.text
    assert "no_runtime_signal_observed" in response.text
    assert "no_dashboard_data" in response.text
    assert "Live ready" not in response.text
    x7_section = response.text.split('data-testid="x7-semantic-status"', maxsplit=1)[1]
    x7_section = x7_section.split("</section>", maxsplit=1)[0]
    assert "100%" not in x7_section


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
