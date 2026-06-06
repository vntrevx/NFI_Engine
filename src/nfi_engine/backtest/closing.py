from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import assert_never

from nfi_engine.backtest.execution import close_trade
from nfi_engine.backtest.frames import candle_close, candle_high, candle_low
from nfi_engine.backtest.models import OpenTrade, SimulationSettings, TradeRecord
from nfi_engine.backtest.pricing import stoploss_trigger_price
from nfi_engine.domain import Candle, PositionSide, SignalType
from nfi_engine.strategy import StrategySignal


@dataclass(frozen=True, slots=True)
class CloseResult:
    open_trades: tuple[OpenTrade, ...]
    closed_trades: tuple[TradeRecord, ...]
    profit: Decimal


def close_stopped_trades(
    *,
    open_trades: tuple[OpenTrade, ...],
    candle: Candle,
    settings: SimulationSettings,
) -> CloseResult:
    remaining: tuple[OpenTrade, ...] = ()
    closed: tuple[TradeRecord, ...] = ()
    profit = Decimal(0)
    for open_trade in open_trades:
        stop_price = stoploss_trigger_price(
            side=open_trade.side,
            entry_price=open_trade.entry_price,
            stoploss_pct=settings.stoploss_pct,
        )
        if _stoploss_hit(side=open_trade.side, candle=candle, stop_price=stop_price):
            trade = _close_trade(
                open_trade=open_trade,
                candle=candle,
                base_exit_price=stop_price,
                settings=settings,
                exit_reason="stoploss",
            )
            closed += (trade,)
            profit += trade.profit
        else:
            remaining += (open_trade,)
    return CloseResult(open_trades=remaining, closed_trades=closed, profit=profit)


def close_signal_trades(
    *,
    open_trades: tuple[OpenTrade, ...],
    candle: Candle,
    settings: SimulationSettings,
    signals: tuple[StrategySignal, ...],
) -> CloseResult:
    remaining = open_trades
    closed: tuple[TradeRecord, ...] = ()
    profit = Decimal(0)
    for signal in signals:
        if signal.signal_type is SignalType.EXIT:
            close_result = _close_first_side_match(
                open_trades=remaining,
                side=signal.side,
                candle=candle,
                settings=settings,
            )
            remaining = close_result.open_trades
            closed += close_result.closed_trades
            profit += close_result.profit
    return CloseResult(open_trades=remaining, closed_trades=closed, profit=profit)


def close_open_trades_at_end(
    *,
    open_trades: tuple[OpenTrade, ...],
    candle: Candle,
    settings: SimulationSettings,
) -> CloseResult:
    closed = tuple(
        _close_trade(
            open_trade=open_trade,
            candle=candle,
            base_exit_price=candle_close(candle),
            settings=settings,
            exit_reason="end_of_data",
        )
        for open_trade in open_trades
    )
    return CloseResult(
        open_trades=(),
        closed_trades=closed,
        profit=sum((trade.profit for trade in closed), Decimal(0)),
    )


def _close_first_side_match(
    *,
    open_trades: tuple[OpenTrade, ...],
    side: PositionSide,
    candle: Candle,
    settings: SimulationSettings,
) -> CloseResult:
    remaining: tuple[OpenTrade, ...] = ()
    closed: tuple[TradeRecord, ...] = ()
    profit = Decimal(0)
    already_closed = False
    for open_trade in open_trades:
        if not already_closed and open_trade.side is side:
            trade = _close_trade(
                open_trade=open_trade,
                candle=candle,
                base_exit_price=candle_close(candle),
                settings=settings,
                exit_reason="signal",
            )
            closed += (trade,)
            profit += trade.profit
            already_closed = True
        else:
            remaining += (open_trade,)
    return CloseResult(open_trades=remaining, closed_trades=closed, profit=profit)


def _stoploss_hit(*, side: PositionSide, candle: Candle, stop_price: Decimal) -> bool:
    match side:
        case PositionSide.LONG:
            return candle_low(candle) <= stop_price
        case PositionSide.SHORT:
            return candle_high(candle) >= stop_price
        case unreachable:
            assert_never(unreachable)


def _close_trade(
    *,
    open_trade: OpenTrade,
    candle: Candle,
    base_exit_price: Decimal,
    settings: SimulationSettings,
    exit_reason: str,
) -> TradeRecord:
    return close_trade(
        open_trade=open_trade,
        candle=candle,
        base_exit_price=base_exit_price,
        settings=settings,
        exit_reason=exit_reason,
    )
