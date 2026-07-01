from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Final

import pytest
from sqlalchemy.exc import IntegrityError

from nfi_engine.domain import OrderType, PositionSide
from nfi_engine.execution.models import ExecutionEventType, ExecutionState
from nfi_engine.persistence import create_persistence_database
from nfi_engine.persistence.records import (
    ExecutionEventRecord,
    ExecutionFillRecord,
    ExecutionIntentRecord,
    ExecutionOrderRecord,
)
from nfi_engine.persistence.repositories import (
    ExecutionEventRepository,
    ExecutionFillRepository,
    ExecutionIntentRepository,
    ExecutionOrderRepository,
)
from nfi_engine.persistence.session import PersistenceDatabase

pytestmark = pytest.mark.anyio

NOW: Final = datetime(2026, 1, 1, 9, 30, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def database(tmp_path: Path) -> AsyncIterator[PersistenceDatabase]:
    db_path = tmp_path / "engine.sqlite"
    database = create_persistence_database(f"sqlite+aiosqlite:///{db_path}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


async def test_execution_ledger_roundtrips_intent_order_fill_and_events(
    database: PersistenceDatabase,
) -> None:
    # Given
    intent = _intent()
    order = _order()
    fill = _fill()
    created_event = _event(ExecutionEventType.INTENT_CREATED, ExecutionState.INTENT_CREATED)
    filled_event = _event(ExecutionEventType.FILL_RECORDED, ExecutionState.FILLED)

    # When
    async with database.session() as session:
        await ExecutionIntentRepository(session).create(intent)
        await ExecutionOrderRepository(session).create(order)
        await ExecutionFillRepository(session).create(fill)
        event_repository = ExecutionEventRepository(session)
        await event_repository.append(created_event)
        await event_repository.append(filled_event)
        await session.commit()
    async with database.session() as session:
        intent_repository = ExecutionIntentRepository(session)
        order_repository = ExecutionOrderRepository(session)
        fill_repository = ExecutionFillRepository(session)
        event_repository = ExecutionEventRepository(session)
        loaded_intent = await intent_repository.get("intent-1")
        recent_intents = await intent_repository.list_recent(limit=10)
        loaded_order = await order_repository.get("execution-order-1")
        listed_orders = await order_repository.list_for_intent("intent-1", limit=10)
        loaded_fills = await fill_repository.list_for_intent(
            "intent-1",
            limit=10,
        )
        fills_for_order = await fill_repository.list_for_order(
            "execution-order-1",
            limit=10,
        )
        loaded_events = await event_repository.list_for_intent(
            "intent-1",
            limit=10,
        )

    # Then
    assert loaded_intent == intent
    assert recent_intents == (intent,)
    assert loaded_order == order
    assert listed_orders == (order,)
    assert loaded_fills == (fill,)
    assert fills_for_order == (fill,)
    assert [event.event_type for event in loaded_events] == [
        ExecutionEventType.INTENT_CREATED,
        ExecutionEventType.FILL_RECORDED,
    ]
    assert [event.state for event in loaded_events] == [
        ExecutionState.INTENT_CREATED,
        ExecutionState.FILLED,
    ]
    assert all(event.event_id is not None for event in loaded_events)
    first_event_id = loaded_events[0].event_id
    second_event_id = loaded_events[1].event_id
    assert first_event_id is not None
    assert second_event_id is not None
    assert first_event_id < second_event_id


async def test_execution_ledger_rejects_duplicate_idempotency_keys(
    database: PersistenceDatabase,
) -> None:
    # Given
    first = _intent(intent_id="intent-a", idempotency_key="idem-shared")
    duplicate = _intent(intent_id="intent-b", idempotency_key="idem-shared")

    # When
    async with database.session() as session:
        await ExecutionIntentRepository(session).create(first)
        await session.commit()
    async with database.session() as session:
        await ExecutionIntentRepository(session).create(duplicate)
        with pytest.raises(IntegrityError):
            await session.commit()


async def test_execution_ledger_redacts_metadata_and_preserves_event_history(
    database: PersistenceDatabase,
) -> None:
    # Given
    intent = _intent(
        metadata_json=(
            '{"api_key":"raw-key","nested":{"signature":"raw-signature"},"safe":"visible"}'
        ),
    )
    submitted_event = _event(
        ExecutionEventType.ORDER_SUBMITTED,
        ExecutionState.SUBMITTED,
        metadata_json='{"token":"raw-token","safe_event":"kept"}',
    )
    acknowledged_event = _event(
        ExecutionEventType.ORDER_ACKNOWLEDGED,
        ExecutionState.ACKNOWLEDGED,
    )

    # When
    async with database.session() as session:
        await ExecutionIntentRepository(session).create(intent)
        event_repository = ExecutionEventRepository(session)
        await event_repository.append(submitted_event)
        await event_repository.append(acknowledged_event)
        await session.commit()
    async with database.session() as session:
        loaded_intent = await ExecutionIntentRepository(session).get("intent-1")
        loaded_events = await ExecutionEventRepository(session).list_for_intent(
            "intent-1",
            limit=10,
        )

    # Then
    assert loaded_intent is not None
    assert "raw-key" not in loaded_intent.metadata_json
    assert "raw-signature" not in loaded_intent.metadata_json
    assert "***redacted***" in loaded_intent.metadata_json
    assert "visible" in loaded_intent.metadata_json
    assert len(loaded_events) == 2
    assert "raw-token" not in loaded_events[0].metadata_json
    assert "kept" in loaded_events[0].metadata_json
    first_event_id = loaded_events[0].event_id
    second_event_id = loaded_events[1].event_id
    assert first_event_id is not None
    assert second_event_id is not None
    assert first_event_id < second_event_id


def _intent(
    intent_id: str = "intent-1",
    idempotency_key: str = "idem-1",
    metadata_json: str = '{"strategy":"X7"}',
) -> ExecutionIntentRecord:
    return ExecutionIntentRecord(
        intent_id=intent_id,
        idempotency_key=idempotency_key,
        client_order_id=f"nfi-x7-{intent_id}",
        pair="BTC/USDT:USDT",
        side=PositionSide.LONG,
        order_type=OrderType.LIMIT,
        requested_quantity=Decimal("0.0105"),
        requested_price=Decimal("65000.25"),
        state=ExecutionState.INTENT_CREATED,
        raw_status_code=None,
        metadata_json=metadata_json,
        created_at=NOW,
        updated_at=NOW,
        exchange_created_at=None,
        exchange_updated_at=None,
    )


def _order() -> ExecutionOrderRecord:
    return ExecutionOrderRecord(
        execution_order_id="execution-order-1",
        intent_id="intent-1",
        client_order_id="nfi-x7-intent-1",
        exchange_order_id="binance-123",
        pair="BTC/USDT:USDT",
        side=PositionSide.LONG,
        order_type=OrderType.LIMIT,
        requested_quantity=Decimal("0.0105"),
        requested_price=Decimal("65000.25"),
        filled_quantity=Decimal("0.0105"),
        average_fill_price=Decimal("64999.75"),
        state=ExecutionState.FILLED,
        raw_status_code="FILLED",
        metadata_json='{"venue":"binance-testnet"}',
        created_at=NOW,
        updated_at=NOW + timedelta(seconds=4),
        exchange_created_at=NOW + timedelta(seconds=1),
        exchange_updated_at=NOW + timedelta(seconds=3),
    )


def _fill() -> ExecutionFillRecord:
    return ExecutionFillRecord(
        execution_fill_id="fill-1",
        intent_id="intent-1",
        execution_order_id="execution-order-1",
        exchange_order_id="binance-123",
        pair="BTC/USDT:USDT",
        side=PositionSide.LONG,
        quantity=Decimal("0.0105"),
        price=Decimal("64999.75"),
        fee_asset="USDT",
        fee_amount=Decimal("0.273"),
        metadata_json='{"liquidity":"taker"}',
        filled_at=NOW + timedelta(seconds=3),
    )


def _event(
    event_type: ExecutionEventType,
    state: ExecutionState,
    metadata_json: str = '{"source":"test"}',
) -> ExecutionEventRecord:
    return ExecutionEventRecord(
        event_id=None,
        intent_id="intent-1",
        event_type=event_type,
        state=state,
        message=event_type.value,
        raw_status_code=None,
        metadata_json=metadata_json,
        occurred_at=NOW + timedelta(seconds=1),
    )
