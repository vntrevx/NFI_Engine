from __future__ import annotations

from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.exchange.capabilities import (
    ExchangeSupportLevel,
    get_exchange_profile,
    list_exchange_profiles,
)


def test_bybit_verified_profile_supports_futures_testnet_order_lane() -> None:
    # Given
    profile = get_exchange_profile("bybit")

    # When / Then
    assert profile is not None
    assert profile.exchange_id == "bybit"
    assert profile.support_level is ExchangeSupportLevel.VERIFIED
    assert profile.supports_trading_mode(TradingMode.FUTURES) is True
    assert profile.supports_testnet is True
    assert profile.supports_sandbox is True
    assert profile.evidence == "tests/integration/exchange/test_bybit_adapter.py"
    assert profile.supports_margin_mode(MarginMode.ISOLATED) is True


def test_binance_profile_stays_candidate_until_order_lane_is_verified() -> None:
    # Given
    profile = get_exchange_profile("binance")

    # When / Then
    assert profile is not None
    assert profile.support_level is ExchangeSupportLevel.CANDIDATE
    assert profile.supports_trading_mode(TradingMode.FUTURES) is True
    assert profile.supports_testnet is True
    assert profile.evidence == "docs/exchange-support-matrix.md"


def test_unknown_exchange_is_not_silently_generic() -> None:
    # Given / When
    profile = get_exchange_profile("typo-exchange")

    # Then
    assert profile is None


def test_seeded_registry_contains_explicit_generic_profile() -> None:
    # Given / When
    profiles = list_exchange_profiles()
    generic = get_exchange_profile("generic-ccxt")

    # Then
    assert generic is not None
    assert generic.support_level is ExchangeSupportLevel.GENERIC_UNVERIFIED
    assert generic.supports_data_only is True
    assert generic.supports_sandbox is False
    assert generic.supports_trailing_stop is False
    assert "bybit" in {profile.exchange_id for profile in profiles}
