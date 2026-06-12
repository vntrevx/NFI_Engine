from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import ClassVar

from pydantic import ConfigDict, field_validator

from nfi_engine.config import Locale
from nfi_engine.config.models import RuntimeSettings, StrictConfigModel
from nfi_engine.domain import MarginMode, TradingMode


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
    risk_preset: RiskPreset = RiskPreset.BALANCED
    margin_mode: MarginMode | None = None
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


@dataclass(frozen=True, slots=True)
class SetupPlan:
    valid: bool
    errors: tuple[str, ...]
    settings: RuntimeSettings | None
    config_text: str
    redacted_config_text: str
    config_path: Path | None = None
