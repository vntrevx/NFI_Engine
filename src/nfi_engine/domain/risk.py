from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Final, Self

from nfi_engine.domain.enums import ErrorCode
from nfi_engine.domain.errors import DomainError
from nfi_engine.domain.primitives import DecimalInput, parse_decimal

MIN_LEVERAGE: Final = Decimal(1)
MAX_LEVERAGE: Final = Decimal(125)
MIN_LIQUIDATION_BUFFER: Final = Decimal(0)
MAX_LIQUIDATION_BUFFER: Final = Decimal("0.99")
DEFAULT_LIQUIDATION_BUFFER: Final = Decimal("0.05")


@dataclass(frozen=True, slots=True)
class Leverage:
    value: Decimal

    @classmethod
    def parse(cls, raw: DecimalInput) -> Self:
        value = parse_decimal(raw, "leverage", ErrorCode.LEVERAGE_OUT_OF_RANGE)
        if value < MIN_LEVERAGE or value > MAX_LEVERAGE:
            raise DomainError(
                code=ErrorCode.LEVERAGE_OUT_OF_RANGE,
                message=f"leverage must be between {MIN_LEVERAGE} and {MAX_LEVERAGE}",
            )
        return cls(value=value)

    @classmethod
    def one(cls) -> Self:
        return cls(value=MIN_LEVERAGE)


@dataclass(frozen=True, slots=True)
class LiquidationBuffer:
    value: Decimal

    @classmethod
    def parse(cls, raw: DecimalInput) -> Self:
        value = parse_decimal(raw, "liquidation_buffer", ErrorCode.LIQUIDATION_BUFFER_OUT_OF_RANGE)
        if value < MIN_LIQUIDATION_BUFFER or value > MAX_LIQUIDATION_BUFFER:
            raise DomainError(
                code=ErrorCode.LIQUIDATION_BUFFER_OUT_OF_RANGE,
                message=(
                    "liquidation_buffer must be between "
                    f"{MIN_LIQUIDATION_BUFFER} and {MAX_LIQUIDATION_BUFFER}"
                ),
            )
        return cls(value=value)

    @classmethod
    def default(cls) -> Self:
        return cls(value=DEFAULT_LIQUIDATION_BUFFER)
