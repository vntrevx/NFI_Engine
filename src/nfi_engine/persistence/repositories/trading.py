from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import select

from nfi_engine.domain import OrderState, OrderType, PositionSide, TradeState
from nfi_engine.persistence.converters import (
    datetime_from_storage,
    datetime_to_storage,
    decimal_from_storage,
    decimal_to_storage,
)
from nfi_engine.persistence.models import OrderRow, PositionRow, TradeRow
from nfi_engine.persistence.records import OrderRecord, PositionRecord, TradeRecord

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class TradeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def create(self, record: TradeRecord) -> None:
        self._session.add(_trade_row(record))

    async def get(self, trade_id: str) -> TradeRecord | None:
        row = await self._session.get(TradeRow, trade_id)
        if row is None:
            return None
        return _trade_record(row)

    async def list_recent(self, *, limit: int) -> tuple[TradeRecord, ...]:
        if limit <= 0:
            return ()
        rows = (
            await self._session.scalars(
                select(TradeRow).order_by(TradeRow.opened_at.desc()).limit(limit),
            )
        ).all()
        return tuple(_trade_record(row) for row in rows)

    async def list_open(self, *, limit: int) -> tuple[TradeRecord, ...]:
        if limit <= 0:
            return ()
        rows = (
            await self._session.scalars(
                select(TradeRow)
                .where(TradeRow.state == TradeState.OPEN.value)
                .order_by(TradeRow.opened_at.desc())
                .limit(limit),
            )
        ).all()
        return tuple(_trade_record(row) for row in rows)

    async def update_state(
        self,
        trade_id: str,
        state: TradeState,
        *,
        closed_at: datetime | None,
        exit_price: Decimal | None,
        profit: Decimal,
    ) -> None:
        row = await self._session.get(TradeRow, trade_id)
        if row is None:
            return
        row.state = state.value
        row.closed_at = None if closed_at is None else datetime_to_storage(closed_at)
        row.exit_price = None if exit_price is None else decimal_to_storage(exit_price)
        row.profit = decimal_to_storage(profit)


class OrderRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def create(self, record: OrderRecord) -> None:
        self._session.add(_order_row(record))

    async def get(self, order_id: str) -> OrderRecord | None:
        row = await self._session.get(OrderRow, order_id)
        if row is None:
            return None
        return _order_record(row)

    async def list_recent(self, *, limit: int) -> tuple[OrderRecord, ...]:
        if limit <= 0:
            return ()
        rows = (
            await self._session.scalars(
                select(OrderRow).order_by(OrderRow.created_at.desc()).limit(limit),
            )
        ).all()
        return tuple(_order_record(row) for row in rows)

    async def list_open(self, *, limit: int) -> tuple[OrderRecord, ...]:
        if limit <= 0:
            return ()
        rows = (
            await self._session.scalars(
                select(OrderRow)
                .where(
                    OrderRow.state.in_(
                        (
                            OrderState.CREATED.value,
                            OrderState.OPEN.value,
                            OrderState.PARTIALLY_FILLED.value,
                        ),
                    ),
                )
                .order_by(OrderRow.created_at.desc())
                .limit(limit),
            )
        ).all()
        return tuple(_order_record(row) for row in rows)

    async def update_state(self, order_id: str, state: OrderState) -> None:
        row = await self._session.get(OrderRow, order_id)
        if row is not None:
            row.state = state.value


class PositionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session: AsyncSession = session

    async def create(self, record: PositionRecord) -> None:
        self._session.add(_position_row(record))

    async def get(self, position_id: str) -> PositionRecord | None:
        row = await self._session.get(PositionRow, position_id)
        if row is None:
            return None
        return _position_record(row)

    async def list_open(self, *, limit: int) -> tuple[PositionRecord, ...]:
        if limit <= 0:
            return ()
        rows = (
            await self._session.scalars(
                select(PositionRow)
                .where(PositionRow.state == TradeState.OPEN.value)
                .order_by(PositionRow.updated_at.desc())
                .limit(limit),
            )
        ).all()
        return tuple(_position_record(row) for row in rows)

    async def update_state(self, position_id: str, state: TradeState) -> None:
        row = await self._session.get(PositionRow, position_id)
        if row is not None:
            row.state = state.value


def _trade_row(record: TradeRecord) -> TradeRow:
    row = TradeRow()
    row.trade_id = record.trade_id
    row.pair = record.pair
    row.side = record.side.value
    row.state = record.state.value
    row.opened_at = datetime_to_storage(record.opened_at)
    row.closed_at = None if record.closed_at is None else datetime_to_storage(record.closed_at)
    row.entry_price = decimal_to_storage(record.entry_price)
    row.exit_price = None if record.exit_price is None else decimal_to_storage(record.exit_price)
    row.quantity = decimal_to_storage(record.quantity)
    row.leverage = decimal_to_storage(record.leverage)
    row.profit = decimal_to_storage(record.profit)
    return row


def _trade_record(row: TradeRow) -> TradeRecord:
    return TradeRecord(
        trade_id=row.trade_id,
        pair=row.pair,
        side=PositionSide(row.side),
        state=TradeState(row.state),
        opened_at=datetime_from_storage(row.opened_at),
        closed_at=None if row.closed_at is None else datetime_from_storage(row.closed_at),
        entry_price=decimal_from_storage(row.entry_price),
        exit_price=None if row.exit_price is None else decimal_from_storage(row.exit_price),
        quantity=decimal_from_storage(row.quantity),
        leverage=decimal_from_storage(row.leverage),
        profit=decimal_from_storage(row.profit),
    )


def _order_row(record: OrderRecord) -> OrderRow:
    row = OrderRow()
    row.order_id = record.order_id
    row.trade_id = record.trade_id
    row.pair = record.pair
    row.side = record.side.value
    row.order_type = record.order_type.value
    row.state = record.state.value
    row.price = decimal_to_storage(record.price)
    row.quantity = decimal_to_storage(record.quantity)
    row.created_at = datetime_to_storage(record.created_at)
    return row


def _order_record(row: OrderRow) -> OrderRecord:
    return OrderRecord(
        order_id=row.order_id,
        trade_id=row.trade_id,
        pair=row.pair,
        side=PositionSide(row.side),
        order_type=OrderType(row.order_type),
        state=OrderState(row.state),
        price=decimal_from_storage(row.price),
        quantity=decimal_from_storage(row.quantity),
        created_at=datetime_from_storage(row.created_at),
    )


def _position_row(record: PositionRecord) -> PositionRow:
    row = PositionRow()
    row.position_id = record.position_id
    row.trade_id = record.trade_id
    row.pair = record.pair
    row.side = record.side.value
    row.state = record.state.value
    row.quantity = decimal_to_storage(record.quantity)
    row.entry_price = decimal_to_storage(record.entry_price)
    row.leverage = decimal_to_storage(record.leverage)
    row.updated_at = datetime_to_storage(record.updated_at)
    return row


def _position_record(row: PositionRow) -> PositionRecord:
    return PositionRecord(
        position_id=row.position_id,
        trade_id=row.trade_id,
        pair=row.pair,
        side=PositionSide(row.side),
        state=TradeState(row.state),
        quantity=decimal_from_storage(row.quantity),
        entry_price=decimal_from_storage(row.entry_price),
        leverage=decimal_from_storage(row.leverage),
        updated_at=datetime_from_storage(row.updated_at),
    )
