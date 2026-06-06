from __future__ import annotations

from decimal import Decimal
from typing import assert_never

from nfi_engine.domain import PositionSide


def entry_fill_price(*, side: PositionSide, close: Decimal, slippage_rate: Decimal) -> Decimal:
    match side:
        case PositionSide.LONG:
            return close * (Decimal(1) + slippage_rate)
        case PositionSide.SHORT:
            return close * (Decimal(1) - slippage_rate)
        case unreachable:
            assert_never(unreachable)


def exit_fill_price(*, side: PositionSide, close: Decimal, slippage_rate: Decimal) -> Decimal:
    match side:
        case PositionSide.LONG:
            return close * (Decimal(1) - slippage_rate)
        case PositionSide.SHORT:
            return close * (Decimal(1) + slippage_rate)
        case unreachable:
            assert_never(unreachable)


def stoploss_trigger_price(
    *,
    side: PositionSide,
    entry_price: Decimal,
    stoploss_pct: Decimal,
) -> Decimal:
    match side:
        case PositionSide.LONG:
            return entry_price * (Decimal(1) - stoploss_pct)
        case PositionSide.SHORT:
            return entry_price * (Decimal(1) + stoploss_pct)
        case unreachable:
            assert_never(unreachable)


def trade_gross_profit(
    *,
    side: PositionSide,
    entry_price: Decimal,
    exit_price: Decimal,
    quantity: Decimal,
) -> Decimal:
    match side:
        case PositionSide.LONG:
            return (exit_price - entry_price) * quantity
        case PositionSide.SHORT:
            return (entry_price - exit_price) * quantity
        case unreachable:
            assert_never(unreachable)


def trade_fees(
    *,
    entry_price: Decimal,
    exit_price: Decimal,
    quantity: Decimal,
    fee_rate: Decimal,
) -> Decimal:
    return ((entry_price * quantity) + (exit_price * quantity)) * fee_rate
