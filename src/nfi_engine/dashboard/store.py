from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from nfi_engine.dashboard.models import (
    DashboardEquityPoint,
    DashboardOpenPosition,
    DashboardReadModels,
    DashboardRecentTrade,
)
from nfi_engine.persistence.records import EquitySnapshotRecord, PositionRecord, TradeRecord
from nfi_engine.persistence.repositories import (
    EquitySnapshotRepository,
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

    async def read_models(self) -> DashboardReadModels:
        await self.database.initialize()
        async with self.database.session() as session:
            equity = await EquitySnapshotRepository(session).list_recent(limit=self.equity_limit)
            positions = await PositionRepository(session).list_open(limit=self.position_limit)
            trades = await TradeRepository(session).list_recent(limit=self.trade_limit)
        return DashboardReadModels(
            equity_points=tuple(_equity_point(record) for record in reversed(equity)),
            open_positions=tuple(_open_position(record) for record in positions),
            recent_trades=tuple(_recent_trade(record) for record in trades),
        )


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
