from __future__ import annotations

from pathlib import Path

import pytest

from nfi_engine.api.models import REDACTED, config_current_response
from nfi_engine.api.settings import validate_api_auth_settings
from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.config.enums import ConfigErrorCode
from nfi_engine.config.models import ApiSettings, EngineSettings, ExchangeSettings, RuntimeSettings
from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.safety import SafetyWarningCode, build_safety_report


def test_api_defaults_bind_to_localhost() -> None:
    # Given: default runtime settings.
    settings = RuntimeSettings()

    # When/Then: the API binds only to localhost by default.
    assert settings.api.host == "127.0.0.1"


def test_weak_api_token_is_rejected_outside_local_environment() -> None:
    # Given: a production runtime with a known weak operator token.
    settings = RuntimeSettings(
        engine=EngineSettings(environment="production"),
        api=ApiSettings.model_validate({"auth_token": "test-token"}),
    )

    # When/Then: startup auth validation returns the operator-facing safety code.
    with pytest.raises(Exception, match="WEAK_API_TOKEN") as exc_info:
        validate_api_auth_settings(settings)
    assert str(exc_info.value).startswith("WEAK_API_TOKEN")


def test_live_trading_without_confirmation_is_rejected_at_config_boundary() -> None:
    # Given: a live config missing explicit confirmation.
    config = Path("tests/fixtures/config/live-without-confirmation.yaml")

    # When/Then: config loading blocks before runtime services see the settings.
    with pytest.raises(ConfigLoadError) as exc_info:
        load_runtime_settings(config)
    assert exc_info.value.code is ConfigErrorCode.LIVE_TRADING_REQUIRES_CONFIRMATION


def test_bybit_futures_testnet_config_is_allowed_for_milestone_one() -> None:
    # Given: the milestone-one futures example config.
    config = Path("examples/futures-paper.yaml")

    # When: runtime settings are parsed.
    settings = load_runtime_settings(config)

    # Then: Bybit stays on testnet with futures mode enabled.
    assert settings.exchange.name == "bybit"
    assert settings.exchange.trading_mode is TradingMode.FUTURES
    assert settings.exchange.testnet is True


def test_futures_safety_report_warns_about_account_exclusivity() -> None:
    # Given: futures settings with leverage enabled.
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="bybit",
            trading_mode=TradingMode.FUTURES,
            margin_mode=MarginMode.ISOLATED,
            testnet=True,
        ),
    )

    # When: a safety report is built.
    report = build_safety_report(settings)

    # Then: operators see the one-bot-per-futures-account assumption.
    assert SafetyWarningCode.FUTURES_ACCOUNT_EXCLUSIVITY in {
        warning.code for warning in report.warnings
    }


def test_config_response_redacts_operator_secrets() -> None:
    # Given: runtime settings containing operator credentials.
    settings = RuntimeSettings(
        exchange=ExchangeSettings.model_validate(
            {"api_key": "api-key", "api_secret": "api-secret"},
        ),
        api=ApiSettings.model_validate({"auth_token": "operator-token"}),
    )

    # When: the frontend config response is built.
    payload = config_current_response(settings)

    # Then: every sensitive value is replaced with the shared redaction marker.
    assert payload.exchange.api_key == REDACTED
    assert payload.exchange.api_secret == REDACTED
    assert payload.api.auth_token == REDACTED
