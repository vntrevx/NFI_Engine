from __future__ import annotations

import re
from dataclasses import dataclass
from re import Pattern
from typing import Final, Self, assert_never

from nfi_engine.domain.enums import ErrorCode, TradingMode
from nfi_engine.domain.errors import DomainError
from nfi_engine.domain.primitives import AssetSymbol, PairSymbol

PAIR_PATTERN: Final[Pattern[str]] = re.compile(
    r"^(?P<base>[A-Z0-9]+)/(?P<quote>[A-Z0-9]+)(?::(?P<settle>[A-Z0-9]+))?$",
)


@dataclass(frozen=True, slots=True)
class TradingPair:
    base: AssetSymbol
    quote: AssetSymbol
    settle: AssetSymbol | None

    @classmethod
    def parse(cls, raw: str, trading_mode: TradingMode) -> Self:
        normalized_raw = raw.strip().upper()
        match_result = PAIR_PATTERN.fullmatch(normalized_raw)
        if match_result is None:
            raise DomainError(code=ErrorCode.MALFORMED_PAIR, message=f"invalid pair format: {raw}")
        pair = cls(
            base=AssetSymbol(match_result.group("base")),
            quote=AssetSymbol(match_result.group("quote")),
            settle=_parse_settle(match_result.group("settle")),
        )
        return pair.require_mode(trading_mode)

    @property
    def normalized(self) -> PairSymbol:
        if self.settle is None:
            return PairSymbol(f"{self.base}/{self.quote}")
        return PairSymbol(f"{self.base}/{self.quote}:{self.settle}")

    def require_mode(self, trading_mode: TradingMode) -> Self:
        match trading_mode:
            case TradingMode.SPOT:
                if self.settle is not None:
                    raise DomainError(
                        code=ErrorCode.SPOT_SETTLE_NOT_ALLOWED,
                        message=f"spot pair cannot include settle asset: {self.normalized}",
                    )
                return self
            case TradingMode.FUTURES:
                if self.settle is None:
                    raise DomainError(
                        code=ErrorCode.FUTURES_SETTLE_REQUIRED,
                        message=(
                            f"futures pair requires base/quote:settle format: {self.normalized}"
                        ),
                    )
                return self
            case unreachable:
                assert_never(unreachable)


def _parse_settle(raw_settle: str | None) -> AssetSymbol | None:
    if raw_settle is None:
        return None
    return AssetSymbol(raw_settle)
