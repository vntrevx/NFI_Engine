from __future__ import annotations

import subprocess
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.config.models import ApiSettings, RuntimeSettings

if TYPE_CHECKING:
    from fastapi import FastAPI

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


@pytest.mark.anyio
async def test_api_denies_cors_by_default() -> None:
    # Given: a default ASGI app with no CORS allowlist middleware.
    client = _client(
        create_app(
            settings=RuntimeSettings(
                api=ApiSettings.model_validate({"auth_token": "local-test-bearer"}),
            ),
        ),
    )

    # When: a cross-origin browser request touches the public ping endpoint.
    response = await client.get("/api/v1/ping", headers={"Origin": "https://evil.example"})

    # Then: the response does not grant cross-origin access.
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_serve_refuses_weak_production_api_token() -> None:
    # Given: a production config with the local QA token value.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "serve",
        "--config",
        "tests/fixtures/config/api-weak-token-prod.yaml",
    ]

    # When: the operator tries to start the API.
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    # Then: startup fails before uvicorn binds the port.
    assert result.returncode == 1
    assert "WEAK_API_TOKEN" in result.stderr


def test_paper_run_blocks_confirmed_live_real_order_config() -> None:
    # Given: a config that passes config confirmation but asks for live real orders.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "paper-run",
        "--config",
        "tests/fixtures/config/live-real-orders.yaml",
        "--ticks",
        "tests/fixtures/ticks/btc_usdt_futures.jsonl",
        "--max-events",
        "1",
    ]

    # When: paper-run receives that config.
    result = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then: milestone-one live-trading scope blocks it before order processing.
    assert result.returncode == 1
    assert "LIVE_TRADING_OUT_OF_SCOPE" in result.stderr


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
