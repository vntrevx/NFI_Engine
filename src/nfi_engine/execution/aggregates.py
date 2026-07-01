from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Final, assert_never

from nfi_engine.domain import PositionSide

DEFAULT_QUOTE_FEE_ASSET: Final = "USDT"
ZERO: Final = Decimal(0)


@dataclass(frozen=True, slots=True)
class ExecutionAggregatePosition:
    pair: str
    side: PositionSide
    quantity: Decimal
    entry_price: Decimal
    leverage: Decimal


@dataclass(frozen=True, slots=True)
class ExecutionAggregatePrice:
    pair: str
    price: Decimal
    captured_at: datetime


@dataclass(frozen=True, slots=True)
class ExecutionAggregateTrade:
    profit: Decimal


@dataclass(frozen=True, slots=True)
class ExecutionAggregateClosedTotals:
    profit: Decimal
    wins: int
    losses: int
    breakeven: int


@dataclass(frozen=True, slots=True)
class ExecutionAggregateOrder:
    requested_quantity: Decimal
    filled_quantity: Decimal


@dataclass(frozen=True, slots=True)
class ExecutionAggregateFill:
    fee_asset: str | None
    fee_amount: Decimal | None


@dataclass(frozen=True, slots=True)
class ExecutionAggregateInput:
    now: datetime
    stale_after: timedelta
    positions: tuple[ExecutionAggregatePosition, ...] = ()
    prices: tuple[ExecutionAggregatePrice, ...] = ()
    closed_trades: tuple[ExecutionAggregateTrade, ...] = ()
    closed_totals: ExecutionAggregateClosedTotals | None = None
    orders: tuple[ExecutionAggregateOrder, ...] = ()
    fills: tuple[ExecutionAggregateFill, ...] = ()
    quote_fee_asset: str = DEFAULT_QUOTE_FEE_ASSET


@dataclass(frozen=True, slots=True)
class ExecutionAggregateSummary:
    open_profit: Decimal | None
    closed_profit: Decimal
    wins: int
    losses: int
    breakeven: int
    open_notional: Decimal | None
    account_exposure: Decimal | None
    realized_quote_fees: Decimal
    partial_fills: int
    stale_data: bool
    stale_pairs: tuple[str, ...]
    confident_open_values: bool


def calculate_execution_aggregate(
    aggregate_input: ExecutionAggregateInput,
) -> ExecutionAggregateSummary:
    stale_pairs = _stale_pairs(aggregate_input)
    closed_profit, wins, losses, breakeven = _closed_trade_totals(aggregate_input)
    if stale_pairs != ():
        return ExecutionAggregateSummary(
            open_profit=None,
            closed_profit=closed_profit,
            wins=wins,
            losses=losses,
            breakeven=breakeven,
            open_notional=None,
            account_exposure=None,
            realized_quote_fees=_realized_quote_fees(aggregate_input),
            partial_fills=_partial_fills(aggregate_input.orders),
            stale_data=True,
            stale_pairs=stale_pairs,
            confident_open_values=False,
        )

    prices = _latest_prices(aggregate_input.prices)
    return ExecutionAggregateSummary(
        open_profit=sum(
            (
                _open_profit(position=position, price=prices[position.pair].price)
                for position in aggregate_input.positions
            ),
            ZERO,
        ),
        closed_profit=closed_profit,
        wins=wins,
        losses=losses,
        breakeven=breakeven,
        open_notional=sum(
            (
                abs(position.quantity) * prices[position.pair].price
                for position in aggregate_input.positions
            ),
            ZERO,
        ),
        account_exposure=sum(
            (
                abs(position.quantity) * prices[position.pair].price * position.leverage
                for position in aggregate_input.positions
            ),
            ZERO,
        ),
        realized_quote_fees=_realized_quote_fees(aggregate_input),
        partial_fills=_partial_fills(aggregate_input.orders),
        stale_data=False,
        stale_pairs=(),
        confident_open_values=True,
    )


def _latest_prices(
    prices: tuple[ExecutionAggregatePrice, ...],
) -> dict[str, ExecutionAggregatePrice]:
    latest: dict[str, ExecutionAggregatePrice] = {}
    for price in prices:
        previous = latest.get(price.pair)
        if previous is None or price.captured_at > previous.captured_at:
            latest[price.pair] = price
    return latest


def _stale_pairs(aggregate_input: ExecutionAggregateInput) -> tuple[str, ...]:
    prices = _latest_prices(aggregate_input.prices)
    stale_pairs: set[str] = set()
    for position in aggregate_input.positions:
        price = prices.get(position.pair)
        if price is None or aggregate_input.now - price.captured_at > aggregate_input.stale_after:
            stale_pairs.add(position.pair)
    return tuple(sorted(stale_pairs))


def _closed_trade_totals(aggregate_input: ExecutionAggregateInput) -> tuple[Decimal, int, int, int]:
    if aggregate_input.closed_totals is not None:
        totals = aggregate_input.closed_totals
        return totals.profit, totals.wins, totals.losses, totals.breakeven

    closed_profit = ZERO
    wins = 0
    losses = 0
    breakeven = 0
    for trade in aggregate_input.closed_trades:
        closed_profit += trade.profit
        if trade.profit > ZERO:
            wins += 1
        elif trade.profit < ZERO:
            losses += 1
        else:
            breakeven += 1
    return closed_profit, wins, losses, breakeven


def _open_profit(*, position: ExecutionAggregatePosition, price: Decimal) -> Decimal:
    quantity = abs(position.quantity)
    match position.side:
        case PositionSide.LONG:
            return (price - position.entry_price) * quantity * position.leverage
        case PositionSide.SHORT:
            return (position.entry_price - price) * quantity * position.leverage
        case unreachable:
            assert_never(unreachable)


def _realized_quote_fees(aggregate_input: ExecutionAggregateInput) -> Decimal:
    return sum(
        (
            fill.fee_amount
            for fill in aggregate_input.fills
            if fill.fee_asset == aggregate_input.quote_fee_asset and fill.fee_amount is not None
        ),
        ZERO,
    )


def _partial_fills(orders: tuple[ExecutionAggregateOrder, ...]) -> int:
    return sum(
        1 for order in orders if ZERO < abs(order.filled_quantity) < abs(order.requested_quantity)
    )
