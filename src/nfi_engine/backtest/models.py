from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from nfi_engine.data import CandleBatch
from nfi_engine.domain import PositionSide, TradingMode, TradingPair
from nfi_engine.strategy import FreqtradeStrategyAdapter


@dataclass(frozen=True, slots=True)
class SimulationSettings:
    trading_mode: TradingMode
    starting_balance: Decimal
    stake_amount: Decimal
    fee_rate: Decimal
    slippage_rate: Decimal
    max_open_trades: int
    leverage: Decimal
    liquidation_buffer: Decimal
    stoploss_pct: Decimal


@dataclass(frozen=True, slots=True)
class BacktestRequest:
    candles: CandleBatch
    adapter: FreqtradeStrategyAdapter
    settings: SimulationSettings
    config_digest: str
    strategy_name: str
    metadata: ReproducibilityMetadata


@dataclass(frozen=True, slots=True)
class OpenTrade:
    trade_id: str
    pair: TradingPair
    side: PositionSide
    opened_at: datetime
    entry_price: Decimal
    quantity: Decimal
    stake_amount: Decimal
    leverage: Decimal
    entry_tag: str | None


@dataclass(frozen=True, slots=True)
class TradeRecord:
    trade_id: str
    pair: TradingPair
    side: PositionSide
    opened_at: datetime
    closed_at: datetime
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    stake_amount: Decimal
    leverage: Decimal
    gross_profit: Decimal
    fees: Decimal
    profit: Decimal
    exit_reason: str
    entry_tag: str | None


@dataclass(frozen=True, slots=True)
class EquityPoint:
    opened_at: datetime
    equity: Decimal


@dataclass(frozen=True, slots=True)
class BacktestSummary:
    starting_balance: Decimal
    final_balance: Decimal
    total_profit: Decimal
    total_profit_pct: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    rejected_entries: int
    max_drawdown: Decimal


@dataclass(frozen=True, slots=True)
class StrategySummary:
    name: str
    timeframe: str
    can_short: bool


@dataclass(frozen=True, slots=True)
class SimulatorScenarioMetadata:
    scenario_hash: str
    seed: int


@dataclass(frozen=True, slots=True)
class ReproducibilityMetadata:
    config_hash: str
    strategy_hash: str
    data_hash: str
    engine_version: str
    git_commit: str | None
    dependency_lock_hash: str
    python_version: str
    created_at: datetime
    command_args: tuple[str, ...]
    simulator: SimulatorScenarioMetadata | None = None


@dataclass(frozen=True, slots=True)
class BacktestResult:
    trades: tuple[TradeRecord, ...]
    equity_curve: tuple[EquityPoint, ...]
    summary: BacktestSummary
    config_digest: str
    strategy: StrategySummary
    metadata: ReproducibilityMetadata
