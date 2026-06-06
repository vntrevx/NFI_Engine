from __future__ import annotations

from dataclasses import dataclass, field, replace
from decimal import Decimal
from typing import assert_never

from nfi_engine.domain import (
    AccountSnapshot,
    Candle,
    Leverage,
    OrderState,
    OrderType,
    PositionSide,
    StakeAmount,
    TradingMode,
    TradingPair,
)
from nfi_engine.exchange.errors import ExchangeError, ExchangeErrorCode
from nfi_engine.exchange.models import (
    ExchangeOrder,
    ExchangeOrderRequest,
    FundingRate,
    Market,
    Tick,
    Ticker,
)


@dataclass(slots=True)
class DeterministicExchangeSimulator:
    """Mutable in-memory simulator that records deterministic order state."""

    ticks: tuple[Tick, ...]
    _orders: dict[str, ExchangeOrder] = field(default_factory=dict, init=False)
    _leverages: dict[str, Leverage] = field(default_factory=dict, init=False)

    async def fetch_markets(self) -> tuple[Market, ...]:
        seen: set[str] = set()
        markets: tuple[Market, ...] = ()
        for tick in self.ticks:
            normalized = str(tick.pair.normalized)
            if normalized not in seen:
                seen.add(normalized)
                markets += (Market(pair=tick.pair, trading_mode=_trading_mode_for_pair(tick.pair)),)
        return markets

    async def fetch_balance(self) -> AccountSnapshot:
        return AccountSnapshot(
            captured_at=self.ticks[0].at,
            equity=StakeAmount(Decimal(1000)),
            available=StakeAmount(Decimal(1000)),
            positions=(),
        )

    async def fetch_ticker(self, pair: TradingPair) -> Ticker:
        tick = self._latest_tick(pair)
        return Ticker(pair=pair, price=tick.price, at=tick.at)

    async def fetch_candles(self, pair: TradingPair, _timeframe: str) -> tuple[Candle, ...]:
        self._latest_tick(pair)
        return ()

    async def create_order(self, request: ExchangeOrderRequest) -> ExchangeOrder:
        tick = self._latest_tick(request.pair)
        state = _fill_state(request=request, tick=tick)
        filled_price = tick.price if state is OrderState.FILLED else None
        order = ExchangeOrder(
            order_id=f"sim-{len(self._orders) + 1}",
            pair=request.pair,
            side=request.side,
            order_type=request.order_type,
            state=state,
            quantity=request.quantity,
            price=request.price,
            filled_price=filled_price,
            live_exchange=False,
        )
        self._orders[order.order_id] = order
        return order

    async def cancel_order(self, order_id: str, pair: TradingPair) -> ExchangeOrder:
        order = await self.fetch_order(order_id=order_id, pair=pair)
        canceled = replace(order, state=OrderState.CANCELED)
        self._orders[order_id] = canceled
        return canceled

    async def fetch_order(self, order_id: str, pair: TradingPair) -> ExchangeOrder:
        order = self._orders.get(order_id)
        if order is None or order.pair != pair:
            raise ExchangeError(
                code=ExchangeErrorCode.ORDER_NOT_FOUND,
                message=f"order not found: {order_id}",
            )
        return order

    async def fetch_funding_rate(self, pair: TradingPair) -> FundingRate:
        tick = self._latest_tick(pair)
        if tick.funding_rate is None:
            return FundingRate(pair=pair, rate=Decimal(0), supported=False)
        return FundingRate(pair=pair, rate=tick.funding_rate, supported=True)

    async def set_leverage(self, pair: TradingPair, leverage: Leverage) -> Leverage:
        self._leverages[str(pair.normalized)] = leverage
        return leverage

    def _latest_tick(self, pair: TradingPair) -> Tick:
        for tick in self.ticks:
            if tick.pair == pair:
                return tick
        raise ExchangeError(
            code=ExchangeErrorCode.TICK_NOT_FOUND,
            message=f"tick not found for pair: {pair.normalized}",
        )


def _fill_state(*, request: ExchangeOrderRequest, tick: Tick) -> OrderState:
    match request.order_type:
        case OrderType.MARKET:
            return OrderState.FILLED
        case OrderType.LIMIT:
            if request.price is None:
                return OrderState.OPEN
            if _limit_crosses(request=request, tick=tick):
                return OrderState.FILLED
            return OrderState.OPEN
        case unreachable:
            assert_never(unreachable)


def _limit_crosses(*, request: ExchangeOrderRequest, tick: Tick) -> bool:
    limit_price = request.price
    if limit_price is None:
        return False
    match request.side:
        case PositionSide.LONG:
            return limit_price >= tick.price
        case PositionSide.SHORT:
            return limit_price <= tick.price
        case unreachable:
            assert_never(unreachable)


def _trading_mode_for_pair(pair: TradingPair) -> TradingMode:
    if pair.settle is None:
        return TradingMode.SPOT
    return TradingMode.FUTURES
