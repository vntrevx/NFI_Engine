from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import assert_never

from nfi_engine.circuit_breakers import CircuitBreakerDecision, ensure_order_intent_allowed
from nfi_engine.domain import (
    AccountSnapshot,
    Leverage,
    LiquidationBuffer,
    OrderState,
    OrderType,
    Position,
    PositionSide,
    Price,
    Quantity,
    StakeAmount,
    TradeId,
    TradeState,
    TradingPair,
)
from nfi_engine.exchange import ExchangeOrderRequest
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.paper.models import PaperRunRequest, PaperTick
from nfi_engine.persistence import PersistenceDatabase
from nfi_engine.persistence.records import OrderRecord, PositionRecord, TradeRecord
from nfi_engine.persistence.repositories import OrderRepository, PositionRepository, TradeRepository
from nfi_engine.risk import (
    AcceptedOrderQuote,
    RejectedOrderQuote,
    RiskRequest,
    pair_locks_from_runtime,
    policy_from_runtime,
)
from nfi_engine.risk.service import quote_order

ZERO: Decimal = Decimal(0)


@dataclass(frozen=True, slots=True)
class SignalTickContext:
    database: PersistenceDatabase
    simulator: DeterministicExchangeSimulator
    request: PaperRunRequest
    tick: PaperTick
    side: PositionSide
    trade_number: int
    breaker_decision: CircuitBreakerDecision


async def process_signal_tick(context: SignalTickContext) -> int:
    ensure_order_intent_allowed(context.breaker_decision)
    open_positions = await _open_positions(context)
    quote = quote_order(
        _risk_request(
            request=context.request,
            tick=context.tick,
            side=context.side,
            open_positions=open_positions,
        ),
    )
    match quote:
        case AcceptedOrderQuote():
            order_request = _order_request_from_quote(quote=quote, tick=context.tick)
            order = await context.simulator.create_order(order_request)
            if order.state is not OrderState.FILLED:
                return 0
            async with context.database.session() as session:
                await TradeRepository(session).create(
                    _trade_record(quote, context.tick, context.trade_number),
                )
                await OrderRepository(session).create(
                    _order_record(quote, context.tick, context.trade_number),
                )
                position = _position_record(quote, context.tick, context.trade_number)
                await PositionRepository(session).create(position)
                await session.commit()
            return 1
        case RejectedOrderQuote():
            return 0
        case unreachable:
            assert_never(unreachable)


def _risk_request(
    *,
    request: PaperRunRequest,
    tick: PaperTick,
    side: PositionSide,
    open_positions: tuple[Position, ...],
) -> RiskRequest:
    current_time = tick.at
    return RiskRequest(
        pair=tick.pair,
        side=side,
        stake=StakeAmount(request.settings.risk.stake_usdt),
        requested_leverage=request.settings.risk.leverage,
        account=_account_snapshot(
            request=request,
            current_time=current_time,
            open_positions=open_positions,
        ),
        policy=policy_from_runtime(request.settings),
        pair_locks=pair_locks_from_runtime(settings=request.settings, current_time=current_time),
        cooldown_until=None,
        current_time=current_time,
    )


def _account_snapshot(
    *,
    request: PaperRunRequest,
    current_time: datetime,
    open_positions: tuple[Position, ...],
) -> AccountSnapshot:
    base = request.account_snapshot
    if base is None:
        return AccountSnapshot(
            captured_at=current_time,
            equity=StakeAmount(Decimal(1000)),
            available=StakeAmount(Decimal(1000)),
            positions=open_positions,
        )
    return AccountSnapshot(
        captured_at=base.captured_at,
        equity=base.equity,
        available=base.available,
        positions=open_positions,
    )


async def _open_positions(context: SignalTickContext) -> tuple[Position, ...]:
    async with context.database.session() as session:
        records = await PositionRepository(session).list_open(
            limit=context.request.settings.risk.max_open_trades,
        )
    return tuple(_position_from_record(record, context.request) for record in records)


def _position_from_record(record: PositionRecord, request: PaperRunRequest) -> Position:
    return Position(
        trade_id=TradeId(record.trade_id),
        pair=TradingPair.parse(record.pair, request.settings.exchange.trading_mode),
        side=record.side,
        quantity=Quantity(record.quantity),
        entry_price=Price(record.entry_price),
        leverage=Leverage.parse(record.leverage),
        liquidation_buffer=LiquidationBuffer.parse(request.settings.risk.liquidation_buffer),
        state=record.state,
    )


def _order_request_from_quote(
    *,
    quote: AcceptedOrderQuote,
    tick: PaperTick,
) -> ExchangeOrderRequest:
    notional = quote.stake * quote.leverage.value
    return ExchangeOrderRequest(
        pair=quote.pair,
        side=quote.side,
        order_type=OrderType.MARKET,
        quantity=Quantity(notional / tick.price),
        price=None,
        leverage=quote.leverage,
    )


def _trade_record(quote: AcceptedOrderQuote, tick: PaperTick, trade_number: int) -> TradeRecord:
    return TradeRecord(
        trade_id=f"paper-{trade_number}",
        pair=str(quote.pair.normalized),
        side=quote.side,
        state=TradeState.OPEN,
        opened_at=tick.at,
        closed_at=None,
        entry_price=tick.price,
        exit_price=None,
        quantity=Quantity((quote.stake * quote.leverage.value) / tick.price),
        leverage=quote.leverage.value,
        profit=ZERO,
    )


def _order_record(quote: AcceptedOrderQuote, tick: PaperTick, trade_number: int) -> OrderRecord:
    return OrderRecord(
        order_id=f"paper-order-{trade_number}",
        trade_id=f"paper-{trade_number}",
        pair=str(quote.pair.normalized),
        side=quote.side,
        order_type=OrderType.MARKET,
        state=OrderState.FILLED,
        price=tick.price,
        quantity=Quantity((quote.stake * quote.leverage.value) / tick.price),
        created_at=tick.at,
    )


def _position_record(
    quote: AcceptedOrderQuote,
    tick: PaperTick,
    trade_number: int,
) -> PositionRecord:
    return PositionRecord(
        position_id=f"paper-position-{trade_number}",
        trade_id=f"paper-{trade_number}",
        pair=str(quote.pair.normalized),
        side=quote.side,
        state=TradeState.OPEN,
        quantity=Quantity((quote.stake * quote.leverage.value) / tick.price),
        entry_price=tick.price,
        leverage=quote.leverage.value,
        updated_at=tick.at,
    )
