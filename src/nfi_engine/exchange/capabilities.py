from __future__ import annotations

from typing import Final

from nfi_engine.exchange.capability_models import (
    ExchangeCapabilityProfile,
    ExchangeSupportLevel,
)
from nfi_engine.exchange.seed_profiles import ALIASES, EXCHANGE_PROFILES

PROFILE_BY_ID: Final = {profile.exchange_id: profile for profile in EXCHANGE_PROFILES}

__all__ = [
    "ExchangeCapabilityProfile",
    "ExchangeSupportLevel",
    "get_exchange_profile",
    "list_exchange_profiles",
    "normalize_exchange_id",
]


def list_exchange_profiles() -> tuple[ExchangeCapabilityProfile, ...]:
    return EXCHANGE_PROFILES


def get_exchange_profile(raw_exchange_id: str) -> ExchangeCapabilityProfile | None:
    normalized = normalize_exchange_id(raw_exchange_id)
    return PROFILE_BY_ID.get(normalized)


def normalize_exchange_id(raw_exchange_id: str) -> str:
    normalized = raw_exchange_id.strip().lower()
    return ALIASES.get(normalized, normalized)
