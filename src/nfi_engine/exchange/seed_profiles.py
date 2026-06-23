from __future__ import annotations

from typing import Final

from nfi_engine.exchange.candidate_profiles import CANDIDATE_PROFILES
from nfi_engine.exchange.capability_models import (
    ExchangeCapabilityProfile,
    ExchangeSupportLevel,
)
from nfi_engine.exchange.profile_constants import (
    CHECKED_ON,
    DOC_EVIDENCE,
    ISOLATED_CROSS,
    KEY_SECRET,
    MARKET_LIMIT,
    SIMULATOR_EVIDENCE,
)

SIMULATOR_PROFILE: Final = ExchangeCapabilityProfile(
    exchange_id="simulator",
    display_name="Deterministic Simulator",
    support_level=ExchangeSupportLevel.VERIFIED,
    supports_spot=True,
    supports_futures=True,
    margin_modes=ISOLATED_CROSS,
    stoploss_order_types=MARKET_LIMIT,
    supports_market_orders=True,
    supports_testnet=True,
    supports_sandbox=True,
    supports_trailing_stop=True,
    supports_data_only=True,
    credential_fields=(),
    evidence=SIMULATOR_EVIDENCE,
    checked_on=CHECKED_ON,
)

GENERIC_CCXT_PROFILE: Final = ExchangeCapabilityProfile(
    exchange_id="generic-ccxt",
    display_name="Generic CCXT Probe",
    support_level=ExchangeSupportLevel.GENERIC_UNVERIFIED,
    supports_spot=False,
    supports_futures=False,
    margin_modes=(),
    stoploss_order_types=(),
    supports_market_orders=False,
    supports_testnet=False,
    supports_sandbox=False,
    supports_trailing_stop=False,
    supports_data_only=True,
    credential_fields=KEY_SECRET,
    evidence=DOC_EVIDENCE,
    checked_on=CHECKED_ON,
)

EXCHANGE_PROFILES: Final = (SIMULATOR_PROFILE, *CANDIDATE_PROFILES, GENERIC_CCXT_PROFILE)

ALIASES: Final[dict[str, str]] = {
    "gate.io": "gateio",
    "gate-io": "gateio",
    "kraken futures": "kraken-futures",
    "kraken_futures": "kraken-futures",
}
