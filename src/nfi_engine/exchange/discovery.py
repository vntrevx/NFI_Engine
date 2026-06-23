from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Final, TypedDict, assert_never

from nfi_engine.domain import TradingMode
from nfi_engine.exchange.capabilities import get_exchange_profile, normalize_exchange_id
from nfi_engine.exchange.capability_models import (
    ExchangeCapabilityProfile,
    ExchangeSupportLevel,
)
from nfi_engine.exchange.errors import ExchangeError, ExchangeErrorCode
from nfi_engine.exchange.profile_constants import CHECKED_ON, DOC_EVIDENCE

MAX_EXCHANGE_ID_LENGTH: Final = 64
ALLOWED_EXCHANGE_ID_CHARS: Final = frozenset(
    "abcdefghijklmnopqrstuvwxyz0123456789._:-",
)


@unique
class ExchangeCapabilitySource(StrEnum):
    REGISTRY = "registry"
    GENERIC_DISCOVERY = "generic-discovery"


class ExchangeCapabilityPayload(TypedDict):
    exchange_id: str
    requested_exchange: str
    display_name: str
    source: str
    support_level: str
    verification_label: str
    trading_mode: str
    trading_mode_supported: bool
    can_configure: bool
    live_trading_allowed: bool
    policy_block: str
    supports_spot: bool
    supports_futures: bool
    margin_modes: list[str]
    stoploss_order_types: list[str]
    supports_market_orders: bool
    supports_testnet: bool
    supports_sandbox: bool
    supports_trailing_stop: bool
    supports_data_only: bool
    credential_fields: list[str]
    evidence: str
    checked_on: str


@dataclass(frozen=True, slots=True)
class ExchangeCapabilityReport:
    requested_exchange: str
    profile: ExchangeCapabilityProfile
    source: ExchangeCapabilitySource
    trading_mode: TradingMode
    trading_mode_supported: bool
    can_configure: bool
    live_trading_allowed: bool
    policy_block: str

    def to_payload(self) -> ExchangeCapabilityPayload:
        return {
            "exchange_id": self.profile.exchange_id,
            "requested_exchange": self.requested_exchange,
            "display_name": self.profile.display_name,
            "source": self.source.value,
            "support_level": self.profile.support_level.value,
            "verification_label": self.profile.support_level.value,
            "trading_mode": self.trading_mode.value,
            "trading_mode_supported": self.trading_mode_supported,
            "can_configure": self.can_configure,
            "live_trading_allowed": self.live_trading_allowed,
            "policy_block": self.policy_block,
            "supports_spot": self.profile.supports_spot,
            "supports_futures": self.profile.supports_futures,
            "margin_modes": [mode.value for mode in self.profile.margin_modes],
            "stoploss_order_types": [
                order_type.value for order_type in self.profile.stoploss_order_types
            ],
            "supports_market_orders": self.profile.supports_market_orders,
            "supports_testnet": self.profile.supports_testnet,
            "supports_sandbox": self.profile.supports_sandbox,
            "supports_trailing_stop": self.profile.supports_trailing_stop,
            "supports_data_only": self.profile.supports_data_only,
            "credential_fields": list(self.profile.credential_fields),
            "evidence": self.profile.evidence,
            "checked_on": self.profile.checked_on.isoformat(),
        }


def build_exchange_capability_report(
    *,
    exchange_id: str,
    trading_mode: TradingMode,
) -> ExchangeCapabilityReport:
    normalized_exchange_id = parse_exchange_id(exchange_id)
    profile = get_exchange_profile(normalized_exchange_id)
    if profile is None:
        generic_profile = _generic_unverified_profile(normalized_exchange_id)
        return _report_for_profile(
            requested_exchange=exchange_id,
            profile=generic_profile,
            source=ExchangeCapabilitySource.GENERIC_DISCOVERY,
            trading_mode=trading_mode,
        )
    return _report_for_profile(
        requested_exchange=exchange_id,
        profile=profile,
        source=ExchangeCapabilitySource.REGISTRY,
        trading_mode=trading_mode,
    )


def build_exchange_capability_document(
    exchange_id: str,
    trading_mode: TradingMode,
) -> ExchangeCapabilityPayload:
    return build_exchange_capability_report(
        exchange_id=exchange_id,
        trading_mode=trading_mode,
    ).to_payload()


def _report_for_profile(
    *,
    requested_exchange: str,
    profile: ExchangeCapabilityProfile,
    source: ExchangeCapabilitySource,
    trading_mode: TradingMode,
) -> ExchangeCapabilityReport:
    trading_mode_supported = profile.supports_trading_mode(trading_mode)
    return ExchangeCapabilityReport(
        requested_exchange=requested_exchange,
        profile=profile,
        source=source,
        trading_mode=trading_mode,
        trading_mode_supported=trading_mode_supported,
        can_configure=_can_configure_profile(
            profile=profile,
            trading_mode_supported=trading_mode_supported,
        ),
        live_trading_allowed=False,
        policy_block=_policy_block(profile),
    )


def parse_exchange_id(raw_exchange_id: str) -> str:
    normalized = normalize_exchange_id(raw_exchange_id)
    if normalized == "":
        raise ExchangeError(
            code=ExchangeErrorCode.EXCHANGE_ID_INVALID,
            message="exchange id is required",
        )
    if len(normalized) > MAX_EXCHANGE_ID_LENGTH:
        raise ExchangeError(
            code=ExchangeErrorCode.EXCHANGE_ID_INVALID,
            message="exchange id must be 64 characters or fewer",
        )
    if any(char not in ALLOWED_EXCHANGE_ID_CHARS for char in normalized):
        raise ExchangeError(
            code=ExchangeErrorCode.EXCHANGE_ID_INVALID,
            message="exchange id contains unsupported characters",
        )
    return normalized


def _generic_unverified_profile(exchange_id: str) -> ExchangeCapabilityProfile:
    return ExchangeCapabilityProfile(
        exchange_id=exchange_id,
        display_name=exchange_id,
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
        credential_fields=(),
        evidence=f"{DOC_EVIDENCE}#generic-unverified-path",
        checked_on=CHECKED_ON,
    )


def _can_configure_profile(
    *,
    profile: ExchangeCapabilityProfile,
    trading_mode_supported: bool,
) -> bool:
    match profile.support_level:
        case ExchangeSupportLevel.VERIFIED | ExchangeSupportLevel.CANDIDATE:
            return trading_mode_supported
        case ExchangeSupportLevel.GENERIC_UNVERIFIED:
            return False
        case unreachable:
            assert_never(unreachable)


def _policy_block(profile: ExchangeCapabilityProfile) -> str:
    match profile.support_level:
        case ExchangeSupportLevel.VERIFIED:
            return "live trading is blocked in current milestone"
        case ExchangeSupportLevel.CANDIDATE:
            return "candidate exchange requires local evidence before live promotion"
        case ExchangeSupportLevel.GENERIC_UNVERIFIED:
            return (
                "generic-unverified exchange requires an explicit registry profile "
                "and local evidence before config, paper/testnet, or live promotion"
            )
        case unreachable:
            assert_never(unreachable)
