from __future__ import annotations

from dataclasses import dataclass

from nfi_engine.domain import TradingMode


@dataclass(frozen=True, slots=True)
class OperatorProfile:
    name: str
    description: str
    trading_modes: tuple[TradingMode, ...]
    requires_testnet: bool
    allow_live_trading: bool
    read_only: bool
    exchange_id: str | None = None
