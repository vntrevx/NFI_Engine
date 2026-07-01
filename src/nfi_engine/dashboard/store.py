from __future__ import annotations

from asyncio import Lock
from dataclasses import dataclass, field
from typing import Protocol

from nfi_engine.dashboard.models import (
    DashboardClosedTradeSummary,
    DashboardEquityPoint,
    DashboardExecutionEvent,
    DashboardExecutionFill,
    DashboardExecutionIntent,
    DashboardExecutionOrder,
    DashboardOpenPosition,
    DashboardReadModels,
    DashboardRecentTrade,
)
from nfi_engine.persistence.records import (
    EquitySnapshotRecord,
    ExecutionEventRecord,
    ExecutionFillRecord,
    ExecutionIntentRecord,
    ExecutionOrderRecord,
    PositionRecord,
    TradeAggregateRecord,
    TradeRecord,
)
from nfi_engine.persistence.repositories import (
    EquitySnapshotRepository,
    ExecutionEventRepository,
    ExecutionFillRepository,
    ExecutionIntentRepository,
    ExecutionOrderRepository,
    PositionRepository,
    TradeRepository,
)
from nfi_engine.persistence.session import PersistenceDatabase


class DashboardReadStore(Protocol):
    async def read_models(self) -> DashboardReadModels: ...


@dataclass(frozen=True, slots=True)
class StaticDashboardReadStore:
    models: DashboardReadModels = field(default_factory=DashboardReadModels.empty)

    async def read_models(self) -> DashboardReadModels:
        return self.models


@dataclass(frozen=True, slots=True)
class PersistenceDashboardReadStore:
    database: PersistenceDatabase
    equity_limit: int = 120
    position_limit: int = 50
    trade_limit: int = 50
    execution_intent_limit: int = 20
    execution_order_limit: int = 20
    execution_fill_limit: int = 50
    execution_event_limit: int = 50
    _initialized: bool = field(default=False, init=False, repr=False, compare=False)
    _initialize_lock: Lock = field(default_factory=Lock, init=False, repr=False, compare=False)

    async def read_models(self) -> DashboardReadModels:
        await self._ensure_initialized()
        async with self.database.session() as session:
            equity = await EquitySnapshotRepository(session).list_recent(limit=self.equity_limit)
            positions = await PositionRepository(session).list_open(limit=self.position_limit)
            trade_repository = TradeRepository(session)
            trades = await trade_repository.list_recent(limit=self.trade_limit)
            closed_trade_summary = await trade_repository.closed_trade_summary()
            execution_intents = await ExecutionIntentRepository(session).list_recent(
                limit=self.execution_intent_limit,
            )
            open_execution_orders = await ExecutionOrderRepository(session).list_open(
                limit=self.execution_order_limit,
            )
            recent_execution_fills = await ExecutionFillRepository(session).list_recent(
                limit=self.execution_fill_limit,
            )
            recent_execution_events = await ExecutionEventRepository(session).list_recent(
                limit=self.execution_event_limit,
            )
        return DashboardReadModels(
            equity_points=tuple(_equity_point(record) for record in reversed(equity)),
            open_positions=tuple(_open_position(record) for record in positions),
            recent_trades=tuple(_recent_trade(record) for record in trades),
            execution_intents=tuple(_execution_intent(record) for record in execution_intents),
            open_execution_orders=tuple(
                _execution_order(record) for record in open_execution_orders
            ),
            recent_execution_fills=tuple(
                _execution_fill(record) for record in recent_execution_fills
            ),
            recent_execution_events=tuple(
                _execution_event(record) for record in recent_execution_events
            ),
            closed_trade_summary=_closed_trade_summary(closed_trade_summary),
        )

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return
        async with self._initialize_lock:
            if self._initialized:
                return
            await self.database.initialize()
            object.__setattr__(self, "_initialized", True)


def _equity_point(record: EquitySnapshotRecord) -> DashboardEquityPoint:
    return DashboardEquityPoint(
        at=record.captured_at,
        equity=record.equity,
        available=record.available,
    )


def _open_position(record: PositionRecord) -> DashboardOpenPosition:
    return DashboardOpenPosition(
        position_id=record.position_id,
        pair=record.pair,
        side=record.side,
        quantity=record.quantity,
        entry_price=record.entry_price,
        leverage=record.leverage,
        updated_at=record.updated_at,
    )


def _recent_trade(record: TradeRecord) -> DashboardRecentTrade:
    return DashboardRecentTrade(
        trade_id=record.trade_id,
        pair=record.pair,
        side=record.side,
        state=record.state,
        opened_at=record.opened_at,
        closed_at=record.closed_at,
        profit=record.profit,
    )


def _execution_intent(record: ExecutionIntentRecord) -> DashboardExecutionIntent:
    return DashboardExecutionIntent(
        intent_id=record.intent_id,
        pair=record.pair,
        side=record.side,
        state=record.state,
        requested_quantity=record.requested_quantity,
        requested_price=record.requested_price,
        updated_at=record.updated_at,
    )


def _execution_order(record: ExecutionOrderRecord) -> DashboardExecutionOrder:
    return DashboardExecutionOrder(
        execution_order_id=record.execution_order_id,
        intent_id=record.intent_id,
        pair=record.pair,
        side=record.side,
        state=record.state,
        requested_quantity=record.requested_quantity,
        requested_price=record.requested_price,
        filled_quantity=record.filled_quantity,
        average_fill_price=record.average_fill_price,
        updated_at=record.updated_at,
    )


def _execution_fill(record: ExecutionFillRecord) -> DashboardExecutionFill:
    return DashboardExecutionFill(
        execution_fill_id=record.execution_fill_id,
        intent_id=record.intent_id,
        execution_order_id=record.execution_order_id,
        pair=record.pair,
        side=record.side,
        quantity=record.quantity,
        price=record.price,
        fee_asset=record.fee_asset,
        fee_amount=record.fee_amount,
        filled_at=record.filled_at,
    )


def _execution_event(record: ExecutionEventRecord) -> DashboardExecutionEvent:
    return DashboardExecutionEvent(
        event_id=record.event_id,
        intent_id=record.intent_id,
        event_type=record.event_type,
        state=record.state,
        message=record.message,
        raw_status_code=record.raw_status_code,
        metadata_json=record.metadata_json,
        occurred_at=record.occurred_at,
    )


def _closed_trade_summary(record: TradeAggregateRecord) -> DashboardClosedTradeSummary:
    return DashboardClosedTradeSummary(
        closed_trades=record.closed_trades,
        wins=record.wins,
        losses=record.losses,
        profit=record.profit,
    )
