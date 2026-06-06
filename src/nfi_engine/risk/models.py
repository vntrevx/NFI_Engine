from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique

from nfi_engine.domain import (
    AccountSnapshot,
    Leverage,
    PositionSide,
    StakeAmount,
    TradingMode,
    TradingPair,
)


@unique
class RiskRejectionCode(StrEnum):
    COOLDOWN_ACTIVE = "COOLDOWN_ACTIVE"
    MAX_OPEN_TRADES = "MAX_OPEN_TRADES"
    PAIR_LOCKED = "PAIR_LOCKED"
    PAIR_MODE_INVALID = "PAIR_MODE_INVALID"
    REAL_LIVE_ORDER_DISABLED = "REAL_LIVE_ORDER_DISABLED"
    SIDE_NOT_ALLOWED = "SIDE_NOT_ALLOWED"
    STAKE_EXCEEDS_AVAILABLE = "STAKE_EXCEEDS_AVAILABLE"
    STAKE_OUT_OF_RANGE = "STAKE_OUT_OF_RANGE"


@dataclass(frozen=True, slots=True)
class RiskPolicy:
    trading_mode: TradingMode
    max_open_trades: int
    max_leverage: Leverage
    stoploss_pct: Decimal
    minimal_roi: Decimal
    paper_trading: bool
    testnet: bool
    live_trading: bool


@dataclass(frozen=True, slots=True)
class PairLock:
    pair: TradingPair
    reason: str
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class RiskRequest:
    pair: TradingPair
    side: PositionSide
    stake: StakeAmount
    requested_leverage: Decimal
    account: AccountSnapshot
    policy: RiskPolicy
    pair_locks: tuple[PairLock, ...]
    cooldown_until: datetime | None
    current_time: datetime


@dataclass(frozen=True, slots=True)
class AcceptedOrderQuote:
    pair: TradingPair
    side: PositionSide
    stake: StakeAmount
    leverage: Leverage
    adjusted: bool
    reason: str | None


@dataclass(frozen=True, slots=True)
class RejectedOrderQuote:
    code: RiskRejectionCode
    message: str


@dataclass(frozen=True, slots=True)
class ExitDecision:
    should_exit: bool
    reason: str | None


type OrderQuote = AcceptedOrderQuote | RejectedOrderQuote
