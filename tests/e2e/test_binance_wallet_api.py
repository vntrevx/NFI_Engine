from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.api.wallet_models import WalletBalanceResponse
from nfi_engine.config.models import RuntimeSettings
from nfi_engine.domain import AccountSnapshot, StakeAmount

if TYPE_CHECKING:
    from fastapi import FastAPI

pytestmark = pytest.mark.anyio
NOW = datetime(2026, 6, 18, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_wallet_balance_api_uses_configured_binance_reader_without_secret_surface() -> None:
    # Given: a Binance futures config with exchange credentials and an injected read-only reader.
    settings = RuntimeSettings.model_validate(
        {
            "exchange": {
                "name": "binance",
                "trading_mode": "futures",
                "margin_mode": "isolated",
                "testnet": False,
                "api_key": "api-key-must-not-leak",
                "api_secret": "api-secret-must-not-leak",
                "permission_withdrawal": "disabled",
            },
            "risk": {"allocation_cap_pct": "0.20", "stake_usdt": "25", "max_open_trades": 2},
        },
    )
    app = create_app(settings=settings, wallet_balance_reader=FakeBalanceReader())
    async with _client(app) as client:
        # When: the operator explicitly fetches wallet balance from the API surface.
        response = await client.post("/api/v1/wallet/balance/fetch")

    # Then: the route returns the normalized balance and never exposes credentials.
    payload = WalletBalanceResponse.model_validate_json(response.content)
    serialized = response.text
    assert response.status_code == 200
    assert payload.status == "fetched"
    assert payload.exchange == "binance"
    assert payload.trading_mode == "futures"
    assert payload.equity == "210.5"
    assert payload.available == "200.25"
    assert payload.allocation_cap_pct == "0.20"
    assert payload.allocation_cap == "40.0500"
    assert payload.configured_allocation_total == "50"
    assert payload.allocation_cap_exceeded is True
    assert payload.permission_audit.withdrawal == "disabled"
    assert payload.permission_audit.live_safe is True
    assert "api-key-must-not-leak" not in serialized
    assert "api-secret-must-not-leak" not in serialized
    assert "api_key" not in serialized
    assert "api_secret" not in serialized


@dataclass(frozen=True, slots=True)
class FakeBalanceReader:
    async def fetch_balance(self) -> AccountSnapshot:
        return AccountSnapshot(
            captured_at=NOW,
            equity=StakeAmount(Decimal("210.5")),
            available=StakeAmount(Decimal("200.25")),
            positions=(),
        )


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
