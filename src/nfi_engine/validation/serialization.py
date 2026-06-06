from __future__ import annotations

from typing import TypedDict

from nfi_engine.backtest import MetadataPayload, metadata_to_payload
from nfi_engine.validation.models import (
    WalkForwardAggregateMetrics,
    WalkForwardResult,
    WalkForwardSplitResult,
)


class WalkForwardSplitPayload(TypedDict):
    role: str
    start: str
    end: str
    candle_count: int
    total_trades: int
    total_profit: str
    final_balance: str


class WalkForwardAggregatePayload(TypedDict):
    total_trades: int
    total_profit: str
    final_balance: str


class WalkForwardPayload(TypedDict):
    splits: list[WalkForwardSplitPayload]
    aggregate_metrics: WalkForwardAggregatePayload
    profitability_claim: bool
    metadata: MetadataPayload


def walk_forward_to_json_payload(result: WalkForwardResult) -> WalkForwardPayload:
    return WalkForwardPayload(
        splits=[_split_payload(split) for split in result.splits],
        aggregate_metrics=_aggregate_payload(result.aggregate_metrics),
        profitability_claim=result.profitability_claim,
        metadata=metadata_to_payload(result.metadata),
    )


def _split_payload(split: WalkForwardSplitResult) -> WalkForwardSplitPayload:
    return WalkForwardSplitPayload(
        role=split.role.value,
        start=split.start.isoformat(),
        end=split.end.isoformat(),
        candle_count=split.candle_count,
        total_trades=split.total_trades,
        total_profit=str(split.total_profit),
        final_balance=str(split.final_balance),
    )


def _aggregate_payload(
    metrics: WalkForwardAggregateMetrics,
) -> WalkForwardAggregatePayload:
    return WalkForwardAggregatePayload(
        total_trades=metrics.total_trades,
        total_profit=str(metrics.total_profit),
        final_balance=str(metrics.final_balance),
    )
