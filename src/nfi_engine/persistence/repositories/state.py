from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert

from nfi_engine.persistence.converters import (
    datetime_from_storage,
    datetime_to_storage,
    decimal_from_storage,
    decimal_to_storage,
)
from nfi_engine.persistence.models import (
    BotStateRow,
    EquitySnapshotRow,
    LockRow,
    StrategyCustomDataRow,
)
from nfi_engine.persistence.records import (
    EquitySnapshotRecord,
    LockRecord,
    StrategyCustomDataRecord,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class LockRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def acquire(self, record: LockRecord) -> None:
        self._session.add(_lock_row(record))

    async def get(self, name: str) -> LockRecord | None:
        row = await self._session.get(LockRow, name)
        if row is None:
            return None
        return _lock_record(row)


class EquitySnapshotRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def add(self, record: EquitySnapshotRecord) -> None:
        self._session.add(_equity_snapshot_row(record))

    async def list_recent(self, *, limit: int) -> tuple[EquitySnapshotRecord, ...]:
        rows = (
            await self._session.scalars(
                select(EquitySnapshotRow)
                .order_by(EquitySnapshotRow.captured_at.desc())
                .limit(limit),
            )
        ).all()
        return tuple(_equity_snapshot_record(row) for row in rows)


class StrategyCustomDataRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def put(self, record: StrategyCustomDataRecord) -> None:
        statement = (
            insert(StrategyCustomDataRow)
            .values(
                strategy_name=record.strategy_name,
                key=record.key,
                value_json=record.value_json,
                updated_at=datetime_to_storage(record.updated_at),
            )
            .on_conflict_do_update(
                index_elements=["strategy_name", "key"],
                set_={
                    "value_json": record.value_json,
                    "updated_at": datetime_to_storage(record.updated_at),
                },
            )
        )
        await self._session.execute(statement)

    async def get(self, strategy_name: str, key: str) -> StrategyCustomDataRecord | None:
        identity = {"strategy_name": strategy_name, "key": key}
        row = await self._session.get(StrategyCustomDataRow, identity)
        if row is None:
            return None
        return _custom_data_record(row)


class BotStateRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def set(self, key: str, value_json: str) -> None:
        statement = (
            insert(BotStateRow)
            .values(key=key, value_json=value_json)
            .on_conflict_do_update(
                index_elements=["key"],
                set_={"value_json": value_json},
            )
        )
        await self._session.execute(statement)

    async def get(self, key: str) -> str | None:
        row = await self._session.get(BotStateRow, key)
        if row is None:
            return None
        return row.value_json


def _lock_row(record: LockRecord) -> LockRow:
    row = LockRow()
    row.name = record.name
    row.owner = record.owner
    row.acquired_at = datetime_to_storage(record.acquired_at)
    row.expires_at = datetime_to_storage(record.expires_at)
    return row


def _lock_record(row: LockRow) -> LockRecord:
    return LockRecord(
        name=row.name,
        owner=row.owner,
        acquired_at=datetime_from_storage(row.acquired_at),
        expires_at=datetime_from_storage(row.expires_at),
    )


def _equity_snapshot_row(record: EquitySnapshotRecord) -> EquitySnapshotRow:
    row = EquitySnapshotRow()
    row.captured_at = datetime_to_storage(record.captured_at)
    row.equity = decimal_to_storage(record.equity)
    row.available = decimal_to_storage(record.available)
    return row


def _equity_snapshot_record(row: EquitySnapshotRow) -> EquitySnapshotRecord:
    return EquitySnapshotRecord(
        captured_at=datetime_from_storage(row.captured_at),
        equity=decimal_from_storage(row.equity),
        available=decimal_from_storage(row.available),
    )


def _custom_data_record(row: StrategyCustomDataRow) -> StrategyCustomDataRecord:
    return StrategyCustomDataRecord(
        strategy_name=row.strategy_name,
        key=row.key,
        value_json=row.value_json,
        updated_at=datetime_from_storage(row.updated_at),
    )
