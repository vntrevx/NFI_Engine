from __future__ import annotations

from typing import NotRequired, TypedDict

from nfi_engine.backtest.models import (
    BacktestResult,
    EquityPoint,
    ReproducibilityMetadata,
    TradeRecord,
)
from nfi_engine.strategy.timeline import TimelinePayload, timeline_to_payload


class TradePayload(TypedDict):
    trade_id: str
    pair: str
    side: str
    opened_at: str
    closed_at: str
    entry_price: str
    exit_price: str
    quantity: str
    stake_amount: str
    leverage: str
    gross_profit: str
    fees: str
    profit: str
    exit_reason: str
    entry_tag: str | None


class EquityPayload(TypedDict):
    opened_at: str
    equity: str


class SummaryPayload(TypedDict):
    starting_balance: str
    final_balance: str
    total_profit: str
    total_profit_pct: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    rejected_entries: int
    max_drawdown: str


class StrategyPayload(TypedDict):
    name: str
    timeframe: str
    can_short: bool


class MetadataPayload(TypedDict):
    config_hash: str
    strategy_hash: str
    data_hash: str
    engine_version: str
    git_commit: str | None
    dependency_lock_hash: str
    python_version: str
    created_at: str
    command_args: list[str]
    simulator: NotRequired[SimulatorMetadataPayload]


class SimulatorMetadataPayload(TypedDict):
    scenario_hash: str
    seed: int


class BacktestPayload(TypedDict):
    trades: list[TradePayload]
    equity_curve: list[EquityPayload]
    summary: SummaryPayload
    config_digest: str
    strategy: StrategyPayload
    metadata: MetadataPayload
    timeline: TimelinePayload


def result_to_json_payload(result: BacktestResult) -> BacktestPayload:
    return BacktestPayload(
        trades=[_trade_payload(trade) for trade in result.trades],
        equity_curve=[_equity_payload(point) for point in result.equity_curve],
        summary=SummaryPayload(
            starting_balance=str(result.summary.starting_balance),
            final_balance=str(result.summary.final_balance),
            total_profit=str(result.summary.total_profit),
            total_profit_pct=str(result.summary.total_profit_pct),
            total_trades=result.summary.total_trades,
            winning_trades=result.summary.winning_trades,
            losing_trades=result.summary.losing_trades,
            rejected_entries=result.summary.rejected_entries,
            max_drawdown=str(result.summary.max_drawdown),
        ),
        config_digest=result.config_digest,
        strategy=StrategyPayload(
            name=result.strategy.name,
            timeframe=result.strategy.timeframe,
            can_short=result.strategy.can_short,
        ),
        metadata=metadata_to_payload(result.metadata),
        timeline=timeline_to_payload(result.timeline),
    )


def metadata_to_payload(metadata: ReproducibilityMetadata) -> MetadataPayload:
    payload = MetadataPayload(
        config_hash=metadata.config_hash,
        strategy_hash=metadata.strategy_hash,
        data_hash=metadata.data_hash,
        engine_version=metadata.engine_version,
        git_commit=metadata.git_commit,
        dependency_lock_hash=metadata.dependency_lock_hash,
        python_version=metadata.python_version,
        created_at=metadata.created_at.isoformat(),
        command_args=list(metadata.command_args),
    )
    if metadata.simulator is not None:
        payload["simulator"] = SimulatorMetadataPayload(
            scenario_hash=metadata.simulator.scenario_hash,
            seed=metadata.simulator.seed,
        )
    return payload


def _trade_payload(trade: TradeRecord) -> TradePayload:
    return TradePayload(
        trade_id=trade.trade_id,
        pair=trade.pair.normalized,
        side=trade.side.value,
        opened_at=trade.opened_at.isoformat(),
        closed_at=trade.closed_at.isoformat(),
        entry_price=str(trade.entry_price),
        exit_price=str(trade.exit_price),
        quantity=str(trade.quantity),
        stake_amount=str(trade.stake_amount),
        leverage=str(trade.leverage),
        gross_profit=str(trade.gross_profit),
        fees=str(trade.fees),
        profit=str(trade.profit),
        exit_reason=trade.exit_reason,
        entry_tag=trade.entry_tag,
    )


def _equity_payload(point: EquityPoint) -> EquityPayload:
    return EquityPayload(opened_at=point.opened_at.isoformat(), equity=str(point.equity))
