from __future__ import annotations

from nfi_engine.domain import TradingMode
from nfi_engine.exchange.capability_models import ExchangeSupportLevel
from nfi_engine.exchange.discovery import (
    ExchangeCapabilityPayload,
    build_exchange_capability_document,
)


def _assert_credential_fields(profile: ExchangeCapabilityPayload) -> None:
    assert all(isinstance(field, str) for field in profile["credential_fields"])


def test_bybit_futures_discovery_reports_verified_profile_and_mode_support() -> None:
    profile = build_exchange_capability_document("bybit", TradingMode.FUTURES)

    assert profile["exchange_id"] == "bybit"
    assert profile["support_level"] == ExchangeSupportLevel.VERIFIED.value
    assert profile["trading_mode"] == TradingMode.FUTURES.value
    assert profile["live_trading_allowed"] is False
    assert profile["policy_block"] == "live trading is blocked in current milestone"
    assert profile["evidence"] == "tests/integration/exchange/test_bybit_adapter.py"
    _assert_credential_fields(profile)
    assert profile["can_configure"] is True
    assert profile["trading_mode_supported"] is True
    assert profile["official_docs_checked"] is True
    assert profile["official_credential_fields"] == ["api_key", "api_secret"]


def test_unknown_mexc_returns_generic_unverified_report_only_document() -> None:
    profile = build_exchange_capability_document("mexc", TradingMode.FUTURES)

    assert profile["exchange_id"] == "mexc"
    assert profile["support_level"] == ExchangeSupportLevel.GENERIC_UNVERIFIED.value
    assert profile["source"] == "generic-discovery"
    assert profile["can_configure"] is False
    assert profile["trading_mode_supported"] is False
    assert profile["live_trading_allowed"] is False
    assert "evidence" in profile["policy_block"].lower()
    assert profile["credential_fields"] == []
    assert profile["official_docs_checked"] is False
    assert profile["official_credential_fields"] == []
    _assert_credential_fields(profile)


def test_hyperliquid_discovery_reports_signer_account_requirement_without_live_promotion() -> None:
    profile = build_exchange_capability_document("hyperliquid", TradingMode.FUTURES)

    assert profile["exchange_id"] == "hyperliquid"
    assert profile["support_level"] == ExchangeSupportLevel.VERIFIED.value
    assert profile["live_trading_allowed"] is False
    assert profile["credential_fields"] == ["account_address", "api_wallet_signer"]
    assert profile["official_docs_checked"] is True
    assert profile["official_credential_fields"] == [
        "account_address",
        "api_wallet_signer",
    ]
    assert profile["official_secret_fields"] == ["api_wallet_signer"]


def test_okx_discovery_reports_passphrase_requirement_separately_from_runtime_fields() -> None:
    profile = build_exchange_capability_document("okx", TradingMode.FUTURES)

    assert profile["official_docs_checked"] is True
    assert "passphrase" in profile["official_credential_fields"]
    assert "passphrase" in profile["official_secret_fields"]
