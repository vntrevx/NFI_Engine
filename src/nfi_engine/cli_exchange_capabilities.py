from __future__ import annotations

import json
from enum import StrEnum, unique
from typing import assert_never

from nfi_engine.domain import TradingMode
from nfi_engine.exchange import (
    ExchangeCapabilityProfile,
    ExchangeCapabilityReport,
    build_exchange_capability_report,
)


@unique
class ExchangeCapabilitiesFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


def build_exchange_capabilities_output(
    *,
    exchange: str,
    trading_mode: TradingMode,
    output_format: ExchangeCapabilitiesFormat,
) -> str:
    report = build_exchange_capability_report(
        exchange_id=exchange,
        trading_mode=trading_mode,
    )
    match output_format:
        case ExchangeCapabilitiesFormat.TEXT:
            return _format_capability_document(report)
        case ExchangeCapabilitiesFormat.JSON:
            return json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n"
        case unreachable:
            assert_never(unreachable)


def _format_capability_document(report: ExchangeCapabilityReport) -> str:
    return (
        f"exchange={report.profile.exchange_id}\n"
        f"requested_exchange={report.requested_exchange}\n"
        f"{format_capability_profile(report.profile)}"
        f"source={report.source.value}\n"
        f"trading_mode={report.trading_mode.value}\n"
        f"trading_mode_supported={str(report.trading_mode_supported).lower()}\n"
        f"can_configure={str(report.can_configure).lower()}\n"
        f"live_trading_allowed={str(report.live_trading_allowed).lower()}\n"
        f"policy_block={report.policy_block}\n"
        f"credential_fields={','.join(report.profile.credential_fields)}\n"
        f"evidence={report.profile.evidence}\n"
        f"checked_on={report.profile.checked_on.isoformat()}\n"
    )


def format_capability_profile(profile: ExchangeCapabilityProfile) -> str:
    return (
        f"display_name={profile.display_name}\n"
        f"support_level={profile.support_level.value}\n"
        f"supports_spot={str(profile.supports_spot).lower()}\n"
        f"supports_futures={str(profile.supports_futures).lower()}\n"
        f"supports_testnet={str(profile.supports_testnet).lower()}\n"
        f"supports_sandbox={str(profile.supports_sandbox).lower()}\n"
        f"supports_trailing_stop={str(profile.supports_trailing_stop).lower()}\n"
        f"supports_data_only={str(profile.supports_data_only).lower()}\n"
        f"supports_market_orders={str(profile.supports_market_orders).lower()}\n"
        "live_exchange=false\n"
    )
