from __future__ import annotations

from decimal import Decimal
from enum import StrEnum, unique
from typing import ClassVar

from pydantic import BaseModel, ConfigDict


@unique
class PairRejectionCode(StrEnum):
    BLACKLISTED = "BLACKLISTED"
    UNSUPPORTED_PAIR = "UNSUPPORTED_PAIR"
    QUOTE_MISMATCH = "QUOTE_MISMATCH"
    LIQUIDITY_TOO_LOW = "LIQUIDITY_TOO_LOW"
    VOLATILITY_TOO_HIGH = "VOLATILITY_TOO_HIGH"
    FUTURES_NOT_SUPPORTED = "FUTURES_NOT_SUPPORTED"
    LEVERAGE_UNSUPPORTED = "LEVERAGE_UNSUPPORTED"


class StrictPairlistModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


class MarketMetadata(StrictPairlistModel):
    pair: str
    quote: str
    futures: bool
    liquidity_usdt: Decimal
    volatility_pct: Decimal
    max_leverage: Decimal


class RejectedPair(StrictPairlistModel):
    pair: str
    reasons: tuple[PairRejectionCode, ...]


class PairlistValidationResult(StrictPairlistModel):
    accepted_pairs: tuple[str, ...]
    rejected_pairs: tuple[RejectedPair, ...]


class PairlistPatchRequest(StrictPairlistModel):
    blacklist: str = ""
    whitelist: str | None = None


class PairlistDraftResponse(StrictPairlistModel):
    draft_id: str
    accepted: bool
    audit_event: str
    preview: PairlistValidationResult


class PairlistApplyResponse(StrictPairlistModel):
    applied: bool
    audit_event: str
    preview: PairlistValidationResult
