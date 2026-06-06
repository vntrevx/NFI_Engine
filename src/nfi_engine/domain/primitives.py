from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import NewType

from nfi_engine.domain.enums import ErrorCode
from nfi_engine.domain.errors import DomainError

type DecimalInput = Decimal | int | str

AssetSymbol = NewType("AssetSymbol", str)
OrderId = NewType("OrderId", str)
PairSymbol = NewType("PairSymbol", str)
Price = NewType("Price", Decimal)
Quantity = NewType("Quantity", Decimal)
SignalId = NewType("SignalId", str)
StakeAmount = NewType("StakeAmount", Decimal)
TradeId = NewType("TradeId", str)


def parse_decimal(raw: DecimalInput, field_name: str, error_code: ErrorCode) -> Decimal:
    try:
        value = Decimal(str(raw))
    except InvalidOperation as exc:
        raise DomainError(
            code=ErrorCode.DECIMAL_PARSE_FAILED, message=f"{field_name} is not numeric"
        ) from exc
    if not value.is_finite():
        raise DomainError(code=error_code, message=f"{field_name} must be finite")
    return value
