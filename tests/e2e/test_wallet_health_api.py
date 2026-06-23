from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.api.runtime_health_models import RuntimeHealthResponse
from nfi_engine.api.wallet_models import WalletBalanceResponse
from nfi_engine.config.models import RuntimeSettings
from nfi_engine.dashboard.store import StaticDashboardReadStore

if TYPE_CHECKING:
    from fastapi import FastAPI

pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_wallet_balance_api_returns_redacted_simulator_balance() -> None:
    # Given: a local simulator app with anonymous loopback operator access.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: the operator fetches wallet balance.
        response = await client.get("/api/v1/wallet/balance")

    # Then: the response is typed, redacted, and fetched through the adapter boundary.
    payload = WalletBalanceResponse.model_validate_json(response.content)
    serialized = response.text
    assert response.status_code == 200
    assert payload.status == "fetched"
    assert payload.code == "WALLET_BALANCE_FETCHED"
    assert payload.equity == "1000"
    assert payload.available == "1000"
    assert payload.allocation_cap_pct == "0.10"
    assert payload.allocation_cap == "100.00"
    assert payload.configured_allocation_total == "30"
    assert payload.allocation_cap_exceeded is False
    assert payload.permission_audit.withdrawal == "unknown"
    assert "api_key" not in serialized
    assert "api_secret" not in serialized
    assert "auth_token" not in serialized


async def test_wallet_balance_fetch_action_returns_live_snapshot_shape() -> None:
    # Given: the explicit operator fetch action.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: Settings asks for a wallet refresh.
        response = await client.post("/api/v1/wallet/balance/fetch")

    # Then: the same typed snapshot shape is returned without browser storage or secrets.
    payload = WalletBalanceResponse.model_validate_json(response.content)
    assert response.status_code == 200
    assert payload.status == "fetched"
    assert payload.available == "1000"
    assert payload.quote_asset == "USDT"
    assert payload.permission_audit.summary.startswith("read=unknown")
    assert payload.allocation_cap == "100.00"


async def test_runtime_health_api_includes_wallet_check_without_secret_surface() -> None:
    # Given: a local app with an empty dashboard store.
    async with _client(
        create_app(settings=RuntimeSettings(), dashboard_store=StaticDashboardReadStore()),
    ) as client:
        # When: runtime health is inspected.
        response = await client.get("/api/v1/runtime/health")

    # Then: health is explicit about degraded data and includes wallet diagnostics.
    payload = RuntimeHealthResponse.model_validate_json(response.content)
    serialized = response.text
    assert response.status_code == 200
    assert payload.state == "degraded"
    assert payload.wallet_balance.code == "WALLET_BALANCE_FETCHED"
    assert payload.wallet_balance.permission_audit.live_safe is True
    assert payload.wallet_balance.allocation_cap_exceeded is False
    assert "WALLET_BALANCE" in {item.code for item in payload.checks}
    assert "DATA_FRESHNESS" in {item.code for item in payload.checks}
    assert "api_key" not in serialized
    assert "api_secret" not in serialized
    assert "auth_token" not in serialized


async def test_wallet_balance_api_blocks_bybit_without_credentials() -> None:
    # Given: a testnet exchange config without credentials.
    settings = RuntimeSettings.model_validate({"exchange": {"name": "bybit", "testnet": True}})
    async with _client(create_app(settings=settings)) as client:
        # When: the wallet endpoint is called.
        response = await client.get("/api/v1/wallet/balance")

    # Then: the operator gets a stable setup action instead of a live call.
    payload = WalletBalanceResponse.model_validate_json(response.content)
    assert response.status_code == 200
    assert payload.status == "blocked"
    assert payload.code == "WALLET_BALANCE_MISSING_CREDENTIALS"
    assert payload.permission_audit.withdrawal == "unknown"
    assert payload.allocation_cap is None
    assert payload.allocation_cap_exceeded is None


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
