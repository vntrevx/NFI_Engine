from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from nfi_engine.execution import OPEN_EXECUTION_STATES
from nfi_engine.persistence.execution_converters import (
    execution_event_record_from_row,
    execution_event_row,
    execution_fill_record_from_row,
    execution_fill_row,
    execution_intent_record_from_row,
    execution_intent_row,
    execution_order_record_from_row,
    execution_order_row,
)
from nfi_engine.persistence.models import (
    ExecutionEventRow,
    ExecutionFillRow,
    ExecutionIntentRow,
    ExecutionOrderRow,
)
from nfi_engine.persistence.records import (
    ExecutionEventRecord,
    ExecutionFillRecord,
    ExecutionIntentRecord,
    ExecutionOrderRecord,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class ExecutionIntentRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def create(self, record: ExecutionIntentRecord) -> None:
        self._session.add(execution_intent_row(record))

    async def get(self, intent_id: str) -> ExecutionIntentRecord | None:
        row = await self._session.get(ExecutionIntentRow, intent_id)
        if row is None:
            return None
        return execution_intent_record_from_row(row)

    async def list_recent(
        self,
        *,
        limit: int,
        created_since: datetime | None = None,
    ) -> tuple[ExecutionIntentRecord, ...]:
        if limit <= 0:
            return ()
        statement = select(ExecutionIntentRow)
        if created_since is not None:
            statement = statement.where(ExecutionIntentRow.created_at >= created_since)
        rows = (
            await self._session.scalars(
                statement.order_by(ExecutionIntentRow.created_at.desc()).limit(limit),
            )
        ).all()
        return tuple(execution_intent_record_from_row(row) for row in rows)

    async def list_open(
        self,
        *,
        limit: int,
        updated_since: datetime | None = None,
    ) -> tuple[ExecutionIntentRecord, ...]:
        if limit <= 0:
            return ()
        statement = select(ExecutionIntentRow).where(
            ExecutionIntentRow.state.in_(tuple(state.value for state in OPEN_EXECUTION_STATES)),
        )
        if updated_since is not None:
            statement = statement.where(ExecutionIntentRow.updated_at >= updated_since)
        rows = (
            await self._session.scalars(
                statement.order_by(ExecutionIntentRow.updated_at.desc()).limit(limit),
            )
        ).all()
        return tuple(execution_intent_record_from_row(row) for row in rows)


class ExecutionOrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def create(self, record: ExecutionOrderRecord) -> None:
        self._session.add(execution_order_row(record))

    async def get(self, execution_order_id: str) -> ExecutionOrderRecord | None:
        row = await self._session.get(ExecutionOrderRow, execution_order_id)
        if row is None:
            return None
        return execution_order_record_from_row(row)

    async def list_open(
        self,
        *,
        limit: int,
        updated_since: datetime | None = None,
    ) -> tuple[ExecutionOrderRecord, ...]:
        if limit <= 0:
            return ()
        statement = select(ExecutionOrderRow).where(
            ExecutionOrderRow.state.in_(tuple(state.value for state in OPEN_EXECUTION_STATES)),
        )
        if updated_since is not None:
            statement = statement.where(ExecutionOrderRow.updated_at >= updated_since)
        rows = (
            await self._session.scalars(
                statement.order_by(ExecutionOrderRow.updated_at.desc()).limit(limit),
            )
        ).all()
        return tuple(execution_order_record_from_row(row) for row in rows)

    async def list_for_intent(
        self,
        intent_id: str,
        *,
        limit: int,
    ) -> tuple[ExecutionOrderRecord, ...]:
        if limit <= 0:
            return ()
        rows = (
            await self._session.scalars(
                select(ExecutionOrderRow)
                .where(ExecutionOrderRow.intent_id == intent_id)
                .order_by(ExecutionOrderRow.created_at.desc())
                .limit(limit),
            )
        ).all()
        return tuple(execution_order_record_from_row(row) for row in rows)


class ExecutionFillRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def create(self, record: ExecutionFillRecord) -> None:
        self._session.add(execution_fill_row(record))

    async def list_for_intent(
        self,
        intent_id: str,
        *,
        limit: int,
    ) -> tuple[ExecutionFillRecord, ...]:
        if limit <= 0:
            return ()
        rows = (
            await self._session.scalars(
                select(ExecutionFillRow)
                .where(ExecutionFillRow.intent_id == intent_id)
                .order_by(ExecutionFillRow.filled_at.asc())
                .limit(limit),
            )
        ).all()
        return tuple(execution_fill_record_from_row(row) for row in rows)

    async def list_for_order(
        self,
        execution_order_id: str,
        *,
        limit: int,
    ) -> tuple[ExecutionFillRecord, ...]:
        if limit <= 0:
            return ()
        rows = (
            await self._session.scalars(
                select(ExecutionFillRow)
                .where(ExecutionFillRow.execution_order_id == execution_order_id)
                .order_by(ExecutionFillRow.filled_at.asc())
                .limit(limit),
            )
        ).all()
        return tuple(execution_fill_record_from_row(row) for row in rows)

    async def list_recent(
        self,
        *,
        limit: int,
        filled_since: datetime | None = None,
    ) -> tuple[ExecutionFillRecord, ...]:
        if limit <= 0:
            return ()
        statement = select(ExecutionFillRow)
        if filled_since is not None:
            statement = statement.where(ExecutionFillRow.filled_at >= filled_since)
        rows = (
            await self._session.scalars(
                statement.order_by(ExecutionFillRow.filled_at.desc()).limit(limit),
            )
        ).all()
        return tuple(execution_fill_record_from_row(row) for row in rows)


class ExecutionEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def append(self, record: ExecutionEventRecord) -> None:
        self._session.add(execution_event_row(record))

    async def list_for_intent(
        self,
        intent_id: str,
        *,
        limit: int,
    ) -> tuple[ExecutionEventRecord, ...]:
        if limit <= 0:
            return ()
        rows = (
            await self._session.scalars(
                select(ExecutionEventRow)
                .where(ExecutionEventRow.intent_id == intent_id)
                .order_by(ExecutionEventRow.event_id.asc())
                .limit(limit),
            )
        ).all()
        return tuple(execution_event_record_from_row(row) for row in rows)

    async def list_recent(
        self,
        *,
        limit: int,
        occurred_since: datetime | None = None,
    ) -> tuple[ExecutionEventRecord, ...]:
        if limit <= 0:
            return ()
        statement = select(ExecutionEventRow)
        if occurred_since is not None:
            statement = statement.where(ExecutionEventRow.occurred_at >= occurred_since)
        rows = (
            await self._session.scalars(
                statement.order_by(ExecutionEventRow.occurred_at.desc()).limit(limit),
            )
        ).all()
        return tuple(execution_event_record_from_row(row) for row in rows)
