from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from nfi_engine.circuit_breakers import (
    CircuitBreakerDecision,
    CircuitBreakerSnapshot,
    ensure_order_intent_allowed,
    evaluate_circuit_breakers,
)
from nfi_engine.circuit_breakers import (
    policy_from_runtime as circuit_policy_from_runtime,
)
from nfi_engine.domain import (
    AccountSnapshot,
    OrderState,
    OrderType,
    PositionSide,
    Quantity,
    StakeAmount,
    TradeState,
)
from nfi_engine.exchange import ExchangeOrderRequest, Tick
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.paper.errors import PaperError, PaperErrorCode
from nfi_engine.paper.lifecycle import apply_bot_command
from nfi_engine.paper.models import (
    BotCommand,
    BotState,
    PaperRunRequest,
    PaperRunResult,
    PaperTick,
)
from nfi_engine.persistence import PersistenceDatabase, create_persistence_database
from nfi_engine.persistence.records import OrderRecord, PositionRecord, TradeRecord
from nfi_engine.persistence.repositories import OrderRepository, PositionRepository, TradeRepository
from nfi_engine.risk import (
    AcceptedOrderQuote,
    RiskRequest,
    pair_locks_from_runtime,
    policy_from_runtime,
)
from nfi_engine.risk.service import quote_order
from nfi_engine.safety import enforce_milestone_live_trading_scope

ZERO: Decimal = Decimal(0)


@dataclass(frozen=True, slots=True)
class SignalTickContext:
    database: PersistenceDatabase
    simulator: DeterministicExchangeSimulator
    request: PaperRunRequest
    tick: PaperTick
    trade_number: int
    breaker_decision: CircuitBreakerDecision


async def run_paper(request: PaperRunRequest) -> PaperRunResult:
    enforce_milestone_live_trading_scope(request.settings)
    _validate_paper_exchange(request)
    state = apply_bot_command(BotState.STOPPED, BotCommand.START)
    database = create_persistence_database(request.database_url)
    await database.initialize()
    simulator = DeterministicExchangeSimulator(ticks=_exchange_ticks(request.ticks))
    processed_events = 0
    created_trades = 0
    blocked_orders = 0
    latest_decision: CircuitBreakerDecision | None = None
    previous_tick: PaperTick | None = None
    try:
        for tick in request.ticks[: request.max_events]:
            processed_events += 1
            latest_decision = _breaker_decision(
                request=request,
                previous_tick=previous_tick,
                current_tick=tick,
            )
            if state is BotState.RUNNING and tick.signal_side is not None:
                if latest_decision.new_orders_blocked:
                    blocked_orders += 1
                else:
                    created_trades += await _process_signal_tick(
                        SignalTickContext(
                            database=database,
                            simulator=simulator,
                            request=request,
                            tick=tick,
                            trade_number=created_trades + 1,
                            breaker_decision=latest_decision,
                        ),
                    )
            previous_tick = tick
        state = apply_bot_command(state, BotCommand.STOP)
        state = apply_bot_command(state, BotCommand.STOP)
        return PaperRunResult(
            processed_events=processed_events,
            created_trades=created_trades,
            live_orders=False,
            final_state=state,
            trading_halted=_trading_halted(latest_decision),
            halted_breaker=_first_breaker(latest_decision),
            new_orders_blocked=blocked_orders > 0,
        )
    finally:
        await database.dispose()


def _validate_paper_exchange(request: PaperRunRequest) -> None:
    if request.settings.exchange.name == "bybit" and not request.settings.exchange.testnet:
        raise PaperError(
            code=PaperErrorCode.LIVE_EXCHANGE_DISABLED_FOR_MILESTONE,
            message="paper-run requires testnet or simulator exchange in milestone 1",
        )


async def _process_signal_tick(context: SignalTickContext) -> int:
    ensure_order_intent_allowed(context.breaker_decision)
    quote = quote_order(_risk_request(request=context.request, tick=context.tick))
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
        case _:
            return 0


def _risk_request(*, request: PaperRunRequest, tick: PaperTick) -> RiskRequest:
    current_time = tick.at
    return RiskRequest(
        pair=tick.pair,
        side=_signal_side(tick),
        stake=StakeAmount(request.settings.risk.stake_usdt),
        requested_leverage=request.settings.risk.leverage,
        account=AccountSnapshot(
            captured_at=current_time,
            equity=StakeAmount(Decimal(1000)),
            available=StakeAmount(Decimal(1000)),
            positions=(),
        ),
        policy=policy_from_runtime(request.settings),
        pair_locks=pair_locks_from_runtime(settings=request.settings, current_time=current_time),
        cooldown_until=None,
        current_time=current_time,
    )


def _signal_side(tick: PaperTick) -> PositionSide:
    side = tick.signal_side
    if side is None:
        return PositionSide.LONG
    return side


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


def _exchange_ticks(ticks: tuple[PaperTick, ...]) -> tuple[Tick, ...]:
    return tuple(Tick(pair=tick.pair, price=tick.price, at=tick.at) for tick in ticks)


def _breaker_decision(
    *,
    request: PaperRunRequest,
    previous_tick: PaperTick | None,
    current_tick: PaperTick,
) -> CircuitBreakerDecision:
    latest_tick_at = current_tick.at if previous_tick is None else previous_tick.at
    return evaluate_circuit_breakers(
        policy=circuit_policy_from_runtime(request.settings),
        snapshot=CircuitBreakerSnapshot(
            realized_pnl_today=ZERO,
            equity_start=StakeAmount(Decimal(1000)),
            equity_current=StakeAmount(Decimal(1000)),
            consecutive_losses=0,
            latest_tick_at=latest_tick_at,
            current_time=current_tick.at,
            api_error_count=0,
            observed_slippage_pct=ZERO,
            funding_rate=ZERO,
            manual_halt=False,
            rejected_order_count=0,
        ),
    )


def _trading_halted(decision: CircuitBreakerDecision | None) -> bool:
    if decision is None:
        return False
    return decision.trading_halted


def _first_breaker(decision: CircuitBreakerDecision | None) -> str | None:
    if decision is None:
        return None
    if len(decision.triggered) == 0:
        return None
    return decision.triggered[0].kind.value
