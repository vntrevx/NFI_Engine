from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique

from nfi_engine.domain import (
    OrderId,
    PositionSide,
    SignalType,
    TradeId,
    TradingPair,
)
from nfi_engine.strategy.errors import StrategyContractError, StrategyErrorCode


@unique
class RunMode(StrEnum):
    BACKTEST = "backtest"
    DRY_RUN = "dry_run"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class StrategyMetadata:
    pair: TradingPair
    timeframe: str
    runmode: RunMode

    def __getitem__(self, key: str) -> str:
        match key:
            case "pair":
                return str(self.pair.normalized)
            case "timeframe":
                return self.timeframe
            case "runmode":
                return self.runmode.value
            case _:
                raise StrategyContractError(
                    code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
                    message=f"unsupported strategy metadata key: {key}",
                )


@dataclass(frozen=True, slots=True)
class StrategySignal:
    pair: TradingPair
    side: PositionSide
    signal_type: SignalType
    tag: str | None = None


@dataclass(frozen=True, slots=True)
class StrategyTrade:
    trade_id: TradeId
    pair: TradingPair
    side: PositionSide


@dataclass(frozen=True, slots=True)
class StrategyOrder:
    order_id: OrderId
    pair: TradingPair
    side: PositionSide


@dataclass(frozen=True, slots=True)
class StrategyInspection:
    name: str
    can_short: bool
    timeframe: str
    detected_callbacks: tuple[str, ...]
