from __future__ import annotations

from nfi_engine.config.models import ExchangeSettings, RuntimeSettings
from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.exchange.capabilities import (
    ExchangeSupportLevel,
    get_exchange_profile,
    list_exchange_profiles,
)
from nfi_engine.exchange.credential_requirements import missing_runtime_credential_fields
from nfi_engine.exchange.official_requirements import get_official_requirement


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


def test_binance_futures_profile_is_verified_after_order_lane_evidence() -> None:
    # Given
    profile = get_exchange_profile("binance")

    # When / Then
    assert profile is not None
    assert profile.support_level is ExchangeSupportLevel.VERIFIED
    assert profile.supports_trading_mode(TradingMode.FUTURES) is True
    assert profile.supports_testnet is True
    assert profile.evidence == "tests/integration/exchange/test_binance_order_test_adapter.py"


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


def test_seeded_exchange_profiles_have_official_requirement_records() -> None:
    profiles = (
        profile
        for profile in list_exchange_profiles()
        if profile.exchange_id not in {"simulator", "generic-ccxt"}
    )

    assert all(get_official_requirement(profile.exchange_id) is not None for profile in profiles)


def test_special_exchange_credential_models_are_documented_officially() -> None:
    bitget = get_official_requirement("bitget")
    bitmart = get_official_requirement("bitmart")
    hyperliquid = get_official_requirement("hyperliquid")
    bitvavo = get_official_requirement("bitvavo")

    assert bitget is not None
    assert "passphrase" in bitget.credential_fields
    assert bitmart is not None
    assert "memo" in bitmart.credential_fields
    assert hyperliquid is not None
    assert hyperliquid.credential_fields == ("account_address", "api_wallet_signer")
    assert bitvavo is not None
    assert "operator_id" in bitvavo.identifier_fields


def test_runtime_credential_readiness_fails_closed_for_extra_required_fields() -> None:
    bitget_settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="bitget",
            trading_mode=TradingMode.FUTURES,
            api_key="k",
            api_secret="s",  # noqa: S106 - test-only placeholder.
        ),
    )
    hyperliquid_settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="hyperliquid",
            trading_mode=TradingMode.FUTURES,
            api_key="k",
            api_secret="s",  # noqa: S106 - test-only placeholder.
        ),
    )

    assert missing_runtime_credential_fields(bitget_settings) == ("passphrase",)
    assert missing_runtime_credential_fields(hyperliquid_settings) == (
        "account_address",
        "api_wallet_signer",
    )


def test_runtime_credentials_follow_official_requirement_source() -> None:
    bitvavo_settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="bitvavo",
            trading_mode=TradingMode.SPOT,
            api_key="k",
            api_secret="s",  # noqa: S106 - test-only placeholder.
        ),
    )
    kraken_futures_settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="kraken-futures",
            trading_mode=TradingMode.FUTURES,
            api_key="k",
            api_secret="s",  # noqa: S106 - test-only placeholder.
        ),
    )

    assert missing_runtime_credential_fields(bitvavo_settings) == ("operator_id",)
    assert missing_runtime_credential_fields(kraken_futures_settings) == ()


def test_runtime_credential_readiness_accepts_exchange_specific_fields() -> None:
    bitget_settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="bitget",
            trading_mode=TradingMode.FUTURES,
            api_key="k",
            api_secret="s",  # noqa: S106 - test-only placeholder.
            passphrase="p",  # noqa: S106 - test-only placeholder.
        ),
    )
    hyperliquid_settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="hyperliquid",
            trading_mode=TradingMode.FUTURES,
            account_address="0xabc",
            api_wallet_signer="signer",
        ),
    )

    assert missing_runtime_credential_fields(bitget_settings) == ()
    assert missing_runtime_credential_fields(hyperliquid_settings) == ()
