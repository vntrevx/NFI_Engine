from __future__ import annotations

import pytest

from nfi_engine.config import ExchangeSettings, RuntimeSettings
from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.profiles import (
    ProfileError,
    default_profile_name,
    get_operator_profile,
    list_operator_profiles,
)


def test_default_profiles_include_required_operator_modes() -> None:
    # Given: the built-in operator profile catalog.
    profiles = list_operator_profiles()

    # When: profile names are collected.
    names = tuple(profile.name for profile in profiles)

    # Then: milestone-one exposes every required operator mode.
    assert names == ("local-paper", "bybit-testnet", "backtest-only", "readonly-debug")


def test_bybit_testnet_profile_requires_testnet_exchange() -> None:
    # Given: the Bybit testnet profile name.
    profile_name = "bybit-testnet"

    # When: the profile is loaded.
    profile = get_operator_profile(profile_name)

    # Then: live exchange mode is not allowed by that profile.
    assert profile.requires_testnet is True
    assert profile.allow_live_trading is False
    assert profile.exchange_id == "bybit"


def test_default_profile_uses_registry_exchange_metadata_for_testnet_profile() -> None:
    # Given: a registry-normalized Bybit testnet futures configuration.
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="ByBit",
            trading_mode=TradingMode.FUTURES,
            margin_mode=MarginMode.ISOLATED,
            testnet=True,
        ),
    )

    # When: the default operator profile is selected.
    profile_name = default_profile_name(settings)

    # Then: the Bybit testnet profile is chosen without a raw exchange-name branch.
    assert profile_name == "bybit-testnet"


def test_unknown_profile_raises_typed_error() -> None:
    # Given/When/Then: unknown profiles fail with a typed operator-facing code.
    with pytest.raises(ProfileError, match="PROFILE_NOT_FOUND"):
        get_operator_profile("unknown")
