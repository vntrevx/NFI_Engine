from __future__ import annotations

from typing import Final

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import TradingMode
from nfi_engine.exchange import get_exchange_profile
from nfi_engine.profiles.errors import ProfileError, ProfileErrorCode
from nfi_engine.profiles.models import OperatorProfile

PROFILE_NAMES: Final = ("local-paper", "bybit-testnet", "backtest-only", "readonly-debug")


def list_operator_profiles() -> tuple[OperatorProfile, ...]:
    return (
        OperatorProfile(
            name="local-paper",
            description="local simulator or paper trading profile",
            trading_modes=(TradingMode.SPOT, TradingMode.FUTURES),
            requires_testnet=True,
            allow_live_trading=False,
            read_only=False,
        ),
        OperatorProfile(
            name="bybit-testnet",
            description="Bybit futures testnet profile",
            trading_modes=(TradingMode.FUTURES,),
            requires_testnet=True,
            allow_live_trading=False,
            read_only=False,
            exchange_id="bybit",
        ),
        OperatorProfile(
            name="backtest-only",
            description="offline validation and backtest profile",
            trading_modes=(TradingMode.SPOT, TradingMode.FUTURES),
            requires_testnet=False,
            allow_live_trading=False,
            read_only=True,
        ),
        OperatorProfile(
            name="readonly-debug",
            description="read-only diagnostics profile",
            trading_modes=(TradingMode.SPOT, TradingMode.FUTURES),
            requires_testnet=False,
            allow_live_trading=False,
            read_only=True,
        ),
    )


def get_operator_profile(name: str) -> OperatorProfile:
    for profile in list_operator_profiles():
        if profile.name == name:
            return profile
    raise ProfileError(
        code=ProfileErrorCode.PROFILE_NOT_FOUND,
        message=f"profile {name} was not found",
    )


def default_profile_name(settings: RuntimeSettings) -> str:
    if settings.ui.read_only:
        return "readonly-debug"
    exchange_profile = get_exchange_profile(settings.exchange.name)
    if settings.exchange.testnet and exchange_profile is not None:
        for profile in list_operator_profiles():
            if profile.exchange_id == exchange_profile.exchange_id and profile.requires_testnet:
                return profile.name
    if settings.paper_run.enabled:
        return "local-paper"
    return "backtest-only"
