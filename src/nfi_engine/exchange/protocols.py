from __future__ import annotations

from typing import Protocol

from nfi_engine.domain import AccountSnapshot, Candle, Leverage, TradingPair
from nfi_engine.exchange.models import (
    ExchangeOrder,
    ExchangeOrderRequest,
    FundingRate,
    Market,
    Ticker,
)


class ExchangeProtocol(Protocol):
    async def fetch_markets(self) -> tuple[Market, ...]: ...

    async def fetch_balance(self) -> AccountSnapshot: ...

    async def fetch_ticker(self, pair: TradingPair) -> Ticker: ...

    async def fetch_candles(self, pair: TradingPair, timeframe: str) -> tuple[Candle, ...]: ...

    async def create_order(self, request: ExchangeOrderRequest) -> ExchangeOrder: ...

    async def cancel_order(self, order_id: str, pair: TradingPair) -> ExchangeOrder: ...

    async def fetch_order(self, order_id: str, pair: TradingPair) -> ExchangeOrder: ...

    async def fetch_funding_rate(self, pair: TradingPair) -> FundingRate: ...

    async def set_leverage(self, pair: TradingPair, leverage: Leverage) -> Leverage: ...
