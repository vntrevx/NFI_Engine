from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from enum import StrEnum, unique
from typing import assert_never

from nfi_engine.domain import MarginMode, OrderType, TradingMode


@unique
class ExchangeSupportLevel(StrEnum):
    VERIFIED = "verified"
    CANDIDATE = "candidate"
    GENERIC_UNVERIFIED = "generic-unverified"


@dataclass(frozen=True, slots=True)
class ExchangeCapabilityProfile:
    exchange_id: str
    display_name: str
    support_level: ExchangeSupportLevel
    supports_spot: bool
    supports_futures: bool
    margin_modes: tuple[MarginMode, ...]
    stoploss_order_types: tuple[OrderType, ...]
    supports_market_orders: bool
    supports_testnet: bool
    supports_sandbox: bool
    supports_trailing_stop: bool
    supports_data_only: bool
    credential_fields: tuple[str, ...]
    evidence: str
    checked_on: date

    def supports_trading_mode(self, trading_mode: TradingMode) -> bool:
        match trading_mode:
            case TradingMode.SPOT:
                return self.supports_spot
            case TradingMode.FUTURES:
                return self.supports_futures
            case unreachable:
                assert_never(unreachable)

    def supports_margin_mode(self, margin_mode: MarginMode) -> bool:
        return margin_mode in self.margin_modes
