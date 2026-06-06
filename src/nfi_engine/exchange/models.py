from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from nfi_engine.domain import (
    Leverage,
    OrderState,
    OrderType,
    PositionSide,
    Price,
    Quantity,
    TradingMode,
    TradingPair,
)


@dataclass(frozen=True, slots=True)
class Market:
    pair: TradingPair
    trading_mode: TradingMode


@dataclass(frozen=True, slots=True)
class Ticker:
    pair: TradingPair
    price: Price
    at: datetime


@dataclass(frozen=True, slots=True)
class Tick:
    pair: TradingPair
    price: Price
    at: datetime
    funding_rate: Decimal | None = None


@dataclass(frozen=True, slots=True)
class ExchangeOrderRequest:
    pair: TradingPair
    side: PositionSide
    order_type: OrderType
    quantity: Quantity
    price: Price | None
    leverage: Leverage


@dataclass(frozen=True, slots=True)
class ExchangeOrder:
    order_id: str
    pair: TradingPair
    side: PositionSide
    order_type: OrderType
    state: OrderState
    quantity: Quantity
    price: Price | None
    filled_price: Price | None
    live_exchange: bool


@dataclass(frozen=True, slots=True)
class FundingRate:
    pair: TradingPair
    rate: Decimal
    supported: bool
