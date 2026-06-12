from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.api.models import REDACTED, SetupPreviewResponse
from nfi_engine.config.models import RuntimeSettings

if TYPE_CHECKING:
    from fastapi import FastAPI


@pytest.mark.anyio
async def test_setup_preview_returns_redacted_valid_config() -> None:
    # Given: a local setup request containing exchange credentials.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: the API previews the generated runtime config.
        response = await client.post(
            "/api/v1/setup/preview",
            json={
                "exchange": "bybit",
                "trading_mode": "futures",
                "intent": "testnet",
                "api_key": "api-preview-key",
                "api_secret": "api-preview-secret",
                "risk_preset": "balanced",
            },
        )

    # Then: the response is valid and every secret-bearing surface is redacted.
    payload = SetupPreviewResponse.model_validate_json(response.content)
    assert response.status_code == 200
    assert payload.valid is True
    assert payload.redacted_config is not None
    assert payload.redacted_config.exchange.api_key == REDACTED
    assert payload.redacted_config.exchange.api_secret == REDACTED
    assert "api-preview-key" not in payload.config_preview
    assert "api-preview-secret" not in payload.config_preview
    assert "trading_mode: 'futures'" in payload.config_preview


@pytest.mark.anyio
async def test_setup_preview_blocks_live_mode_without_confirmation() -> None:
    # Given: a live setup request without explicit confirmation.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: setup preview validates the request.
        response = await client.post(
            "/api/v1/setup/preview",
            json={
                "exchange": "bybit",
                "trading_mode": "spot",
                "intent": "live",
                "api_key": "api-live-key",
                "api_secret": "api-live-secret",
                "risk_preset": "conservative",
            },
        )

    # Then: the safety gate reports the same live confirmation requirement.
    payload = SetupPreviewResponse.model_validate_json(response.content)
    assert response.status_code == 200
    assert payload.valid is False
    assert payload.redacted_config is None
    assert "LIVE_TRADING_REQUIRES_CONFIRMATION" in payload.errors
    assert "api-live-key" not in payload.config_preview
    assert "api-live-secret" not in payload.config_preview


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
