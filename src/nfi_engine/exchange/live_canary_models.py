from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


@unique
class LiveCanaryCheckState(StrEnum):
    CLEAR = "clear"
    BLOCK = "block"


@unique
class LiveCanaryCheckCode(StrEnum):
    CONFIG_ENABLED = "LIVE_CANARY_CONFIG_ENABLED"
    PRODUCTION_SCOPE = "LIVE_CANARY_PRODUCTION_SCOPE"
    REQUIRED_FIELDS = "LIVE_CANARY_REQUIRED_FIELDS"
    PAIR_VALID = "LIVE_CANARY_PAIR_VALID"
    CONFIRMATION = "LIVE_CANARY_CONFIRMATION"
    CREDENTIALS = "LIVE_CANARY_CREDENTIALS"
    PERMISSIONS = "LIVE_CANARY_PERMISSIONS"
    MANUAL_HALT = "LIVE_CANARY_MANUAL_HALT"
    RECONCILIATION_FRESHNESS = "LIVE_CANARY_RECONCILIATION_FRESHNESS"
    WALLET_FRESHNESS = "LIVE_CANARY_WALLET_FRESHNESS"


class LiveCanaryCheck(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    code: LiveCanaryCheckCode
    state: LiveCanaryCheckState
    message: str
    next_action: str


class LiveCanaryPreview(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    ready: bool
    preview_hash: str
    exchange: str
    testnet: bool
    production: bool
    trading_mode: str | None
    pair: str | None
    order_type: str | None
    canary_notional_usdt: Decimal | None
    leverage: Decimal | None
    max_loss_estimate_usdt: Decimal | None
    fee_estimate_usdt: Decimal | None
    kill_switch_state: str
    reconciliation_captured_at: datetime | None
    reconciliation_age_seconds: int | None
    wallet_balance_captured_at: datetime | None
    wallet_balance_age_seconds: int | None
    rollback_command: str
    required_confirmation_phrase: str
    confirmation_phrase_matches: bool
    credentials_present: bool
    permission_summary: str
    adapter_constructed: bool
    order_would_be_submitted: bool
    checks: tuple[LiveCanaryCheck, ...]
    blockers: tuple[str, ...]
