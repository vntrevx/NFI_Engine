from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Final

import pytest

from nfi_engine.dashboard.store import PersistenceDashboardReadStore
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
FUTURE: Final = NOW + timedelta(days=1)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def database(tmp_path: Path) -> AsyncIterator[PersistenceDatabase]:
    db_path = tmp_path / "execution-read-models.sqlite"
    database = create_persistence_database(f"sqlite+aiosqlite:///{db_path}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


async def test_dashboard_store_returns_bounded_execution_read_models(
    database: PersistenceDatabase,
) -> None:
    async with database.session() as session:
        intents = ExecutionIntentRepository(session)
        orders = ExecutionOrderRepository(session)
        fills = ExecutionFillRepository(session)
        events = ExecutionEventRepository(session)
        await intents.create(_intent("intent-old", NOW - timedelta(minutes=3)))
        await intents.create(_intent("intent-new", NOW))
        await orders.create(
            _order("order-filled", "intent-old", ExecutionState.FILLED, NOW),
        )
        await orders.create(
            _order("order-open", "intent-new", ExecutionState.ACKNOWLEDGED, NOW),
        )
        await fills.create(
            _fill(
                "fill-old",
                "intent-old",
                "order-filled",
                NOW - timedelta(minutes=1),
            ),
        )
        await fills.create(_fill("fill-new", "intent-new", "order-open", NOW))
        await events.append(_event("intent-old", ExecutionEventType.INTENT_CREATED, NOW))
        await events.append(_event("intent-new", ExecutionEventType.ORDER_ACKNOWLEDGED, NOW))
        await session.commit()

    store = PersistenceDashboardReadStore(
        database,
        execution_intent_limit=1,
        execution_order_limit=5,
        execution_fill_limit=1,
        execution_event_limit=1,
    )

    models = await store.read_models()

    assert tuple(intent.intent_id for intent in models.execution_intents) == ("intent-new",)
    assert tuple(order.execution_order_id for order in models.open_execution_orders) == (
        "order-open",
    )
    assert models.open_execution_orders[0].requested_quantity == Decimal("0.01")
    assert tuple(fill.execution_fill_id for fill in models.recent_execution_fills) == ("fill-new",)
    assert models.recent_execution_fills[0].fee_amount == Decimal("0.10")
    assert tuple(event.intent_id for event in models.recent_execution_events) == ("intent-new",)


async def test_execution_repositories_return_empty_for_zero_limit_and_future_window(
    database: PersistenceDatabase,
) -> None:
    async with database.session() as session:
        await ExecutionIntentRepository(session).create(_intent("intent-1", NOW))
        await ExecutionOrderRepository(session).create(
            _order("order-1", "intent-1", ExecutionState.SUBMITTED, NOW),
        )
        await ExecutionFillRepository(session).create(_fill())
        await ExecutionEventRepository(session).append(
            _event("intent-1", ExecutionEventType.ORDER_SUBMITTED, NOW),
        )
        await session.commit()

    async with database.session() as session:
        intents = ExecutionIntentRepository(session)
        orders = ExecutionOrderRepository(session)
        fills = ExecutionFillRepository(session)
        events = ExecutionEventRepository(session)

        assert await intents.list_recent(limit=0) == ()
        assert await intents.list_recent(limit=5, created_since=FUTURE) == ()
        assert await orders.list_open(limit=0) == ()
        assert await orders.list_open(limit=5, updated_since=FUTURE) == ()
        assert await fills.list_recent(limit=0) == ()
        assert await fills.list_recent(limit=5, filled_since=FUTURE) == ()
        assert await events.list_recent(limit=0) == ()
        assert await events.list_recent(limit=5, occurred_since=FUTURE) == ()


def _intent(
    intent_id: str,
    created_at: datetime,
    state: ExecutionState = ExecutionState.INTENT_CREATED,
) -> ExecutionIntentRecord:
    return ExecutionIntentRecord(
        intent_id=intent_id,
        idempotency_key=f"idem-{intent_id}",
        client_order_id=f"client-{intent_id}",
        pair="BTC/USDT:USDT",
        side=PositionSide.LONG,
        order_type=OrderType.LIMIT,
        requested_quantity=Decimal("0.01"),
        requested_price=Decimal(65000),
        state=state,
        raw_status_code=None,
        metadata_json="{}",
        created_at=created_at,
        updated_at=created_at,
        exchange_created_at=None,
        exchange_updated_at=None,
    )


def _order(
    execution_order_id: str,
    intent_id: str,
    state: ExecutionState,
    created_at: datetime,
) -> ExecutionOrderRecord:
    return ExecutionOrderRecord(
        execution_order_id=execution_order_id,
        intent_id=intent_id,
        client_order_id=f"client-{intent_id}",
        exchange_order_id=f"exchange-{execution_order_id}",
        pair="BTC/USDT:USDT",
        side=PositionSide.LONG,
        order_type=OrderType.LIMIT,
        requested_quantity=Decimal("0.01"),
        requested_price=Decimal(65000),
        filled_quantity=Decimal(0),
        average_fill_price=None,
        state=state,
        raw_status_code=state.value,
        metadata_json="{}",
        created_at=created_at,
        updated_at=created_at,
        exchange_created_at=None,
        exchange_updated_at=None,
    )


def _fill(
    execution_fill_id: str = "fill-1",
    intent_id: str = "intent-1",
    execution_order_id: str = "order-1",
    filled_at: datetime = NOW,
) -> ExecutionFillRecord:
    return ExecutionFillRecord(
        execution_fill_id=execution_fill_id,
        intent_id=intent_id,
        execution_order_id=execution_order_id,
        exchange_order_id=f"exchange-{execution_order_id}",
        pair="BTC/USDT:USDT",
        side=PositionSide.LONG,
        quantity=Decimal("0.01"),
        price=Decimal(65000),
        fee_asset="USDT",
        fee_amount=Decimal("0.10"),
        metadata_json="{}",
        filled_at=filled_at,
    )


def _event(
    intent_id: str,
    event_type: ExecutionEventType,
    occurred_at: datetime,
) -> ExecutionEventRecord:
    return ExecutionEventRecord(
        event_id=None,
        intent_id=intent_id,
        event_type=event_type,
        state=ExecutionState.ACKNOWLEDGED,
        message=event_type.value,
        raw_status_code=None,
        metadata_json="{}",
        occurred_at=occurred_at,
    )
