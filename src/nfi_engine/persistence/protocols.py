from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol

from nfi_engine.domain import OrderState, TradeState
from nfi_engine.persistence.records import (
    EquitySnapshotRecord,
    LockRecord,
    OrderRecord,
    PositionRecord,
    StrategyCustomDataRecord,
    TradeRecord,
)


class TradeRepositoryProtocol(Protocol):
    async def create(self, record: TradeRecord) -> None: ...

    async def get(self, trade_id: str) -> TradeRecord | None: ...

    async def list_recent(self, *, limit: int) -> tuple[TradeRecord, ...]: ...

    async def list_open(self, *, limit: int) -> tuple[TradeRecord, ...]: ...

    async def update_state(
        self,
        trade_id: str,
        state: TradeState,
        *,
        closed_at: datetime | None,
        exit_price: Decimal | None,
        profit: Decimal,
    ) -> None: ...


class OrderRepositoryProtocol(Protocol):
    async def create(self, record: OrderRecord) -> None: ...

    async def get(self, order_id: str) -> OrderRecord | None: ...

    async def list_recent(self, *, limit: int) -> tuple[OrderRecord, ...]: ...

    async def list_open(self, *, limit: int) -> tuple[OrderRecord, ...]: ...

    async def update_state(self, order_id: str, state: OrderState) -> None: ...


class PositionRepositoryProtocol(Protocol):
    async def create(self, record: PositionRecord) -> None: ...

    async def get(self, position_id: str) -> PositionRecord | None: ...

    async def list_open(self, *, limit: int) -> tuple[PositionRecord, ...]: ...

    async def update_state(self, position_id: str, state: TradeState) -> None: ...


class LockRepositoryProtocol(Protocol):
    async def acquire(self, record: LockRecord) -> None: ...

    async def get(self, name: str) -> LockRecord | None: ...

    async def list_active(self, *, now: datetime, limit: int) -> tuple[LockRecord, ...]: ...


class EquitySnapshotRepositoryProtocol(Protocol):
    async def add(self, record: EquitySnapshotRecord) -> None: ...

    async def list_recent(self, *, limit: int) -> tuple[EquitySnapshotRecord, ...]: ...


class StrategyCustomDataRepositoryProtocol(Protocol):
    async def put(self, record: StrategyCustomDataRecord) -> None: ...

    async def get(self, strategy_name: str, key: str) -> StrategyCustomDataRecord | None: ...


__all__ = [
    "EquitySnapshotRepositoryProtocol",
    "LockRepositoryProtocol",
    "OrderRepositoryProtocol",
    "PositionRepositoryProtocol",
    "StrategyCustomDataRepositoryProtocol",
    "TradeRepositoryProtocol",
]
