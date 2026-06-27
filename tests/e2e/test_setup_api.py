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
                "allocated_amount_usdt": "42.5",
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
    assert "stake_usdt: '42.5'" in payload.config_preview
    assert "leverage: '3'" in payload.config_preview


@pytest.mark.anyio
async def test_setup_preview_renders_permission_audit_and_risk_profile() -> None:
    # Given: a testnet setup request with explicit exchange API permission states.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: the API previews the generated runtime config.
        response = await client.post(
            "/api/v1/setup/preview",
            json={
                "exchange": "bybit",
                "trading_mode": "futures",
                "intent": "testnet",
                "api_key": "api-permission-key",
                "api_secret": "api-permission-secret",
                "risk_profile": "balanced",
                "allocated_amount_usdt": "42.5",
                "permission_read": "enabled",
                "permission_trade": "enabled",
                "permission_futures": "enabled",
                "permission_withdrawal": "disabled",
                "permission_ip_allowlist": "unknown",
            },
        )

    # Then: the preview is valid, redacted, and includes deterministic safety fields.
    payload = SetupPreviewResponse.model_validate_json(response.content)
    assert response.status_code == 200
    assert payload.valid is True
    assert "api-permission-key" not in payload.config_preview
    assert "api-permission-secret" not in payload.config_preview
    assert "risk_profile: 'balanced'" in payload.config_preview
    assert "expert_risk_confirmed: false" in payload.config_preview
    assert "permission_withdrawal: 'disabled'" in payload.config_preview
    assert "permission_ip_allowlist: 'unknown'" in payload.config_preview


@pytest.mark.anyio
async def test_setup_preview_accepts_and_redacts_exchange_specific_credentials() -> None:
    # Given: a Bitget setup request uses the official passphrase credential.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: the API previews the generated runtime config.
        response = await client.post(
            "/api/v1/setup/preview",
            json={
                "exchange": "bitget",
                "trading_mode": "futures",
                "intent": "testnet",
                "api_key": "bitget-api-key",
                "api_secret": "bitget-api-secret",
                "passphrase": "bitget-passphrase",
                "allocated_amount_usdt": "42.5",
            },
        )

    # Then: the passphrase is accepted for validation and redacted from the preview.
    payload = SetupPreviewResponse.model_validate_json(response.content)
    assert response.status_code == 200
    assert payload.valid is True
    assert payload.redacted_config is not None
    assert payload.redacted_config.exchange.passphrase == REDACTED
    assert f"passphrase: '{REDACTED}'" in payload.config_preview
    assert "bitget-passphrase" not in payload.config_preview
    assert "bitget-api-secret" not in payload.config_preview


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


@pytest.mark.anyio
async def test_setup_preview_blocks_live_when_withdrawal_permission_is_enabled() -> None:
    # Given: a live setup request with exchange withdrawal permission enabled.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: setup preview validates the request.
        response = await client.post(
            "/api/v1/setup/preview",
            json={
                "exchange": "bybit",
                "trading_mode": "futures",
                "intent": "live",
                "api_key": "api-live-withdraw-key",
                "api_secret": "api-live-withdraw-secret",
                "risk_profile": "safe",
                "live_trading_confirmed": True,
                "permission_withdrawal": "enabled",
            },
        )

    # Then: the permission gate blocks live setup without leaking credentials.
    payload = SetupPreviewResponse.model_validate_json(response.content)
    assert response.status_code == 200
    assert payload.valid is False
    assert "EXCHANGE_WITHDRAWAL_PERMISSION_ENABLED" in payload.errors
    assert "api-live-withdraw-key" not in payload.config_preview
    assert "api-live-withdraw-secret" not in payload.config_preview


@pytest.mark.anyio
async def test_setup_preview_blocks_expert_profile_without_confirmation() -> None:
    # Given: an expert setup request without explicit expert-risk confirmation.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: setup preview validates the request.
        response = await client.post(
            "/api/v1/setup/preview",
            json={
                "exchange": "bybit",
                "trading_mode": "futures",
                "intent": "testnet",
                "risk_profile": "expert",
            },
        )

    # Then: the expert profile requires an explicit operator confirmation.
    payload = SetupPreviewResponse.model_validate_json(response.content)
    assert response.status_code == 200
    assert payload.valid is False
    assert payload.errors == ("EXPERT_RISK_REQUIRES_CONFIRMATION",)


@pytest.mark.anyio
async def test_setup_preview_rejects_malformed_permission_status() -> None:
    # Given: a setup request with an invalid permission enum value.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: the setup preview boundary parses the request.
        response = await client.post(
            "/api/v1/setup/preview",
            json={
                "exchange": "bybit",
                "trading_mode": "futures",
                "intent": "paper",
                "permission_withdrawal": "sometimes",
            },
        )

    # Then: Pydantic rejects it before any config preview is produced.
    assert response.status_code == 422


@pytest.mark.anyio
async def test_setup_preview_rejects_forbidden_secret_fields_without_echo() -> None:
    # Given: a setup preview request containing forbidden wallet and login-token fields.
    raw_values = (
        "seed-value-should-not-echo",
        "private-value-should-not-echo",
        "mnemonic-value-should-not-echo",
        "withdrawal-value-should-not-echo",
        "api-auth-token-should-not-echo",
        "login-token-should-not-echo",
    )
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: the API boundary rejects the extra fields.
        response = await client.post(
            "/api/v1/setup/preview",
            json={
                "exchange": "bybit",
                "trading_mode": "futures",
                "intent": "testnet",
                "wallet_seed": raw_values[0],
                "private_key": raw_values[1],
                "mnemonic": raw_values[2],
                "withdrawal_key": raw_values[3],
                "api_auth_token": raw_values[4],
                "login_token": raw_values[5],
            },
        )

    # Then: validation reports the rejected fields without echoing rejected secrets.
    assert response.status_code == 422
    assert '"input"' not in response.text
    for value in raw_values:
        assert value not in response.text


@pytest.mark.anyio
async def test_setup_preview_rejects_non_positive_allocated_amount() -> None:
    # Given: a setup request with a non-positive allocated trading amount.
    async with _client(create_app(settings=RuntimeSettings())) as client:
        # When: the setup preview boundary parses the request.
        response = await client.post(
            "/api/v1/setup/preview",
            json={
                "exchange": "bybit",
                "trading_mode": "futures",
                "intent": "paper",
                "allocated_amount_usdt": "0",
            },
        )

    # Then: Pydantic rejects it before any config preview is produced.
    assert response.status_code == 422


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
