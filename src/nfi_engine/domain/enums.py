from __future__ import annotations

from enum import StrEnum, unique


@unique
class TradingMode(StrEnum):
    SPOT = "spot"
    FUTURES = "futures"


@unique
class MarginMode(StrEnum):
    ISOLATED = "isolated"
    CROSS = "cross"


@unique
class PositionSide(StrEnum):
    LONG = "long"
    SHORT = "short"


@unique
class OrderType(StrEnum):
    MARKET = "market"
    LIMIT = "limit"


@unique
class TimeInForce(StrEnum):
    GTC = "gtc"
    IOC = "ioc"
    FOK = "fok"


@unique
class OrderState(StrEnum):
    CREATED = "created"
    OPEN = "open"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"


@unique
class TradeState(StrEnum):
    PLANNED = "planned"
    OPEN = "open"
    CLOSED = "closed"
    HALTED = "halted"


@unique
class SignalType(StrEnum):
    ENTER = "enter"
    EXIT = "exit"
    HOLD = "hold"


@unique
class ErrorCode(StrEnum):
    DECIMAL_PARSE_FAILED = "DECIMAL_PARSE_FAILED"
    FUTURES_SETTLE_REQUIRED = "FUTURES_SETTLE_REQUIRED"
    LEVERAGE_OUT_OF_RANGE = "LEVERAGE_OUT_OF_RANGE"
    LIQUIDATION_BUFFER_OUT_OF_RANGE = "LIQUIDATION_BUFFER_OUT_OF_RANGE"
    MALFORMED_PAIR = "MALFORMED_PAIR"
    SPOT_SETTLE_NOT_ALLOWED = "SPOT_SETTLE_NOT_ALLOWED"
    SPOT_SHORT_NOT_ALLOWED = "SPOT_SHORT_NOT_ALLOWED"
