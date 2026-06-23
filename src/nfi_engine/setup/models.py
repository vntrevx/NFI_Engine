from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum, unique
from pathlib import Path
from typing import ClassVar

from pydantic import ConfigDict, field_validator

from nfi_engine.config import Locale
from nfi_engine.config.enums import RiskProfileName
from nfi_engine.config.models import RuntimeSettings, StrictConfigModel
from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.exchange.permissions import ExchangeApiPermissionState


@unique
class SetupIntent(StrEnum):
    PAPER = "paper"
    TESTNET = "testnet"
    LIVE = "live"


@unique
class RiskPreset(StrEnum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class SetupRequest(StrictConfigModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    exchange: str
    trading_mode: TradingMode
    intent: SetupIntent = SetupIntent.PAPER
    api_key: str = ""
    api_secret: str = ""
    risk_profile: RiskProfileName = RiskProfileName.BALANCED
    risk_preset: RiskPreset | None = None
    expert_risk_confirmed: bool = False
    allocated_amount_usdt: Decimal | None = None
    margin_mode: MarginMode | None = None
    permission_read: ExchangeApiPermissionState = ExchangeApiPermissionState.UNKNOWN
    permission_trade: ExchangeApiPermissionState = ExchangeApiPermissionState.UNKNOWN
    permission_futures: ExchangeApiPermissionState = ExchangeApiPermissionState.UNKNOWN
    permission_withdrawal: ExchangeApiPermissionState = ExchangeApiPermissionState.UNKNOWN
    permission_ip_allowlist: ExchangeApiPermissionState = ExchangeApiPermissionState.UNKNOWN
    live_trading_confirmed: bool = False
    locale: Locale = Locale.EN

    @field_validator("exchange", "api_key", "api_secret")
    @classmethod
    def _strip_safe_text(cls, value: str) -> str:
        normalized = value.strip()
        if "\n" in normalized or "\r" in normalized:
            message = "setup text fields must be single-line"
            raise ValueError(message)
        return normalized

    @field_validator("allocated_amount_usdt")
    @classmethod
    def _positive_allocated_amount(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= Decimal(0):
            message = "allocated amount must be greater than 0"
            raise ValueError(message)
        return value


@dataclass(frozen=True, slots=True)
class SetupPlan:
    valid: bool
    errors: tuple[str, ...]
    settings: RuntimeSettings | None
    config_text: str
    redacted_config_text: str
    config_path: Path | None = None
