from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import assert_never

from nfi_engine.backtest.frames import candle_close
from nfi_engine.backtest.models import OpenTrade, SimulationSettings, TradeRecord
from nfi_engine.backtest.pricing import (
    entry_fill_price,
    exit_fill_price,
    trade_fees,
    trade_gross_profit,
)
from nfi_engine.domain import Candle, PositionSide, SignalType, TradingMode
from nfi_engine.strategy import StrategySignal


@dataclass(frozen=True, slots=True)
class EntryResult:
    open_trades: tuple[OpenTrade, ...]
    rejected_entries: int


@dataclass(frozen=True, slots=True)
class EntryContext:
    candle: Candle
    settings: SimulationSettings
    next_trade_number: int
    can_short: bool


def open_signal_trades(
    *,
    open_trades: tuple[OpenTrade, ...],
    signals: tuple[StrategySignal, ...],
    context: EntryContext,
) -> EntryResult:
    current = open_trades
    rejected_entries = 0
    for signal in signals:
        if signal.signal_type is SignalType.ENTER:
            if _entry_rejected(
                signal=signal,
                settings=context.settings,
                current_open_count=len(current),
                can_short=context.can_short,
            ):
                rejected_entries += 1
            else:
                current += (
                    _open_trade(
                        signal=signal,
                        candle=context.candle,
                        settings=context.settings,
                        trade_number=context.next_trade_number + len(current),
                    ),
                )
    return EntryResult(open_trades=current, rejected_entries=rejected_entries)


def close_trade(
    *,
    open_trade: OpenTrade,
    candle: Candle,
    base_exit_price: Decimal,
    settings: SimulationSettings,
    exit_reason: str,
) -> TradeRecord:
    exit_price = exit_fill_price(
        side=open_trade.side,
        close=base_exit_price,
        slippage_rate=settings.slippage_rate,
    )
    gross_profit = trade_gross_profit(
        side=open_trade.side,
        entry_price=open_trade.entry_price,
        exit_price=exit_price,
        quantity=open_trade.quantity,
    )
    fees = trade_fees(
        entry_price=open_trade.entry_price,
        exit_price=exit_price,
        quantity=open_trade.quantity,
        fee_rate=settings.fee_rate,
    )
    return TradeRecord(
        trade_id=open_trade.trade_id,
        pair=open_trade.pair,
        side=open_trade.side,
        opened_at=open_trade.opened_at,
        closed_at=candle.opened_at,
        entry_price=open_trade.entry_price,
        exit_price=exit_price,
        quantity=open_trade.quantity,
        stake_amount=open_trade.stake_amount,
        leverage=open_trade.leverage,
        gross_profit=gross_profit,
        fees=fees,
        profit=gross_profit - fees,
        exit_reason=exit_reason,
        entry_tag=open_trade.entry_tag,
    )


def _entry_rejected(
    *,
    signal: StrategySignal,
    settings: SimulationSettings,
    current_open_count: int,
    can_short: bool,
) -> bool:
    if current_open_count >= settings.max_open_trades:
        return True
    match signal.side:
        case PositionSide.LONG:
            return False
        case PositionSide.SHORT:
            return settings.trading_mode is TradingMode.SPOT or not can_short
        case unreachable:
            assert_never(unreachable)


def _open_trade(
    *,
    signal: StrategySignal,
    candle: Candle,
    settings: SimulationSettings,
    trade_number: int,
) -> OpenTrade:
    entry_price = entry_fill_price(
        side=signal.side,
        close=candle_close(candle),
        slippage_rate=settings.slippage_rate,
    )
    notional = settings.stake_amount * settings.leverage
    return OpenTrade(
        trade_id=f"bt-{trade_number}",
        pair=signal.pair,
        side=signal.side,
        opened_at=candle.opened_at,
        entry_price=entry_price,
        quantity=notional / entry_price,
        stake_amount=settings.stake_amount,
        leverage=settings.leverage,
        entry_tag=signal.tag,
    )
