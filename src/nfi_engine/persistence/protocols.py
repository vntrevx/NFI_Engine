from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Protocol

from nfi_engine.domain import OrderState, TradeState
from nfi_engine.persistence.records import (
    EquitySnapshotRecord,
    ExecutionEventRecord,
    ExecutionFillRecord,
    ExecutionIntentRecord,
    ExecutionOrderRecord,
    LockRecord,
    OrderRecord,
    PositionRecord,
    StrategyCustomDataRecord,
    TradeAggregateRecord,
    TradeRecord,
)


class TradeRepositoryProtocol(Protocol):
    async def create(self, record: TradeRecord) -> None: ...

    async def get(self, trade_id: str) -> TradeRecord | None: ...

    async def list_recent(self, *, limit: int) -> tuple[TradeRecord, ...]: ...

    async def list_open(self, *, limit: int) -> tuple[TradeRecord, ...]: ...

    async def closed_trade_summary(self) -> TradeAggregateRecord: ...

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


class ExecutionIntentRepositoryProtocol(Protocol):
    async def create(self, record: ExecutionIntentRecord) -> None: ...

    async def get(self, intent_id: str) -> ExecutionIntentRecord | None: ...

    async def list_recent(
        self,
        *,
        limit: int,
        created_since: datetime | None = None,
    ) -> tuple[ExecutionIntentRecord, ...]: ...

    async def list_open(
        self,
        *,
        limit: int,
        updated_since: datetime | None = None,
    ) -> tuple[ExecutionIntentRecord, ...]: ...


class ExecutionOrderRepositoryProtocol(Protocol):
    async def create(self, record: ExecutionOrderRecord) -> None: ...

    async def get(self, execution_order_id: str) -> ExecutionOrderRecord | None: ...

    async def list_open(
        self,
        *,
        limit: int,
        updated_since: datetime | None = None,
    ) -> tuple[ExecutionOrderRecord, ...]: ...

    async def list_for_intent(
        self,
        intent_id: str,
        *,
        limit: int,
    ) -> tuple[ExecutionOrderRecord, ...]: ...


class ExecutionFillRepositoryProtocol(Protocol):
    async def create(self, record: ExecutionFillRecord) -> None: ...

    async def list_for_intent(
        self,
        intent_id: str,
        *,
        limit: int,
    ) -> tuple[ExecutionFillRecord, ...]: ...

    async def list_for_order(
        self,
        execution_order_id: str,
        *,
        limit: int,
    ) -> tuple[ExecutionFillRecord, ...]: ...

    async def list_recent(
        self,
        *,
        limit: int,
        filled_since: datetime | None = None,
    ) -> tuple[ExecutionFillRecord, ...]: ...


class ExecutionEventRepositoryProtocol(Protocol):
    async def append(self, record: ExecutionEventRecord) -> None: ...

    async def list_for_intent(
        self,
        intent_id: str,
        *,
        limit: int,
    ) -> tuple[ExecutionEventRecord, ...]: ...

    async def list_recent(
        self,
        *,
        limit: int,
        occurred_since: datetime | None = None,
    ) -> tuple[ExecutionEventRecord, ...]: ...


__all__ = [
    "EquitySnapshotRepositoryProtocol",
    "ExecutionEventRepositoryProtocol",
    "ExecutionFillRepositoryProtocol",
    "ExecutionIntentRepositoryProtocol",
    "ExecutionOrderRepositoryProtocol",
    "LockRepositoryProtocol",
    "OrderRepositoryProtocol",
    "PositionRepositoryProtocol",
    "StrategyCustomDataRepositoryProtocol",
    "TradeRepositoryProtocol",
]
