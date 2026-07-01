from __future__ import annotations

import subprocess
import sys
from decimal import Decimal
from pathlib import Path
from typing import Final

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.config import load_runtime_settings
from nfi_engine.config.models import UiSettings
from nfi_engine.exchange.live_canary_models import LiveCanaryPreview

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
FIXTURE: Final = Path("tests/fixtures/config/live-canary-preview.yaml")
DUMMY_API_KEY: Final = "local-live-canary-key"
DUMMY_API_PRIVATE_VALUE: Final = "local-live-canary-secret"


def test_exchange_live_canary_cli_reports_read_only_preview_json() -> None:
    # Given: the explicit live canary preview fixture.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "live-canary",
        "--preview",
        "--config",
        str(FIXTURE),
        "--json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    validation = subprocess.run(
        [sys.executable, "-m", "json.tool"],
        cwd=PROJECT_ROOT,
        input=result.stdout,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = LiveCanaryPreview.model_validate_json(result.stdout)

    # Then
    assert result.returncode == 0, result.stderr
    assert validation.returncode == 0, validation.stderr
    assert payload.ready is True
    assert payload.production is True
    assert payload.testnet is False
    assert payload.exchange == "binance"
    assert payload.canary_notional_usdt == Decimal("7.50")
    assert payload.leverage == Decimal(2)
    assert payload.adapter_constructed is False
    assert payload.order_would_be_submitted is False
    assert payload.blockers == ()
    assert DUMMY_API_KEY not in result.stdout
    assert DUMMY_API_PRIVATE_VALUE not in result.stdout
    assert DUMMY_API_PRIVATE_VALUE not in result.stderr


def test_exchange_live_canary_cli_blocks_missing_confirmation(tmp_path: Path) -> None:
    # Given: a canary config with the explicit confirmation phrase removed.
    config = tmp_path / "missing-confirmation.yaml"
    config.write_text(
        FIXTURE.read_text(encoding="utf-8").replace(
            "  confirmation_phrase: CONFIRM_LIVE_CANARY_PREVIEW\n",
            "",
        ),
        encoding="utf-8",
    )
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "live-canary",
        "--preview",
        "--config",
        str(config),
        "--json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    payload = LiveCanaryPreview.model_validate_json(result.stdout)

    # Then
    assert result.returncode == 0, result.stderr
    assert payload.ready is False
    assert "LIVE_CANARY_REQUIRED_FIELDS" in payload.blockers
    assert "LIVE_CANARY_CONFIRMATION" in payload.blockers
    assert payload.adapter_constructed is False
    assert payload.order_would_be_submitted is False
    assert DUMMY_API_PRIVATE_VALUE not in result.stdout


def test_exchange_live_canary_cli_refuses_non_preview_execution() -> None:
    # Given: the live canary command without the mandatory preview flag.
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "live-canary",
        "--config",
        str(FIXTURE),
        "--json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 1
    assert result.stdout == ""
    assert "LIVE_CANARY_PREVIEW_REQUIRED" in result.stderr
    assert DUMMY_API_PRIVATE_VALUE not in result.stderr


@pytest.mark.anyio
async def test_live_canary_preview_api_is_protected_read_only_and_redacted() -> None:
    # Given: the protected API running in read-only UI mode.
    base_settings = load_runtime_settings(FIXTURE)
    settings = base_settings.model_copy(update={"ui": UiSettings(read_only=True)})
    async with AsyncClient(
        transport=ASGITransport(app=create_app(settings=settings, config_path=FIXTURE)),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/api/v1/exchange/live-canary/preview")
        write_attempt = await client.post("/api/v1/exchange/live-canary/preview")
        payload = LiveCanaryPreview.model_validate_json(response.content)

    # Then
    assert response.status_code == 200
    assert write_attempt.status_code == 405
    assert payload.ready is True
    assert payload.adapter_constructed is False
    assert payload.order_would_be_submitted is False
    assert DUMMY_API_KEY.encode() not in response.content
    assert DUMMY_API_PRIVATE_VALUE.encode() not in response.content
