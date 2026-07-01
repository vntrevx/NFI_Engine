from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Final, assert_never

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.api.dashboard_models import DashboardSnapshotResponse
from nfi_engine.config.models import DatabaseSettings, RuntimeSettings
from nfi_engine.dashboard.store import PersistenceDashboardReadStore
from nfi_engine.domain import OrderState, OrderType, PositionSide, TradeState
from nfi_engine.persistence import create_persistence_database
from nfi_engine.persistence.records import (
    EquitySnapshotRecord,
    LockRecord,
    OrderRecord,
    PositionRecord,
    TradeRecord,
)
from nfi_engine.persistence.repositories import (
    EquitySnapshotRepository,
    LockRepository,
    OrderRepository,
    PositionRepository,
    TradeRepository,
)
from nfi_engine.persistence.session import PersistenceDatabase

pytestmark = pytest.mark.anyio

NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def database(tmp_path: Path) -> AsyncIterator[PersistenceDatabase]:
    db_path = tmp_path / "dashboard.sqlite"
    database = create_persistence_database(f"sqlite+aiosqlite:///{db_path}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


async def test_trading_repositories_return_bounded_dashboard_lists(
    database: PersistenceDatabase,
) -> None:
    # Given: mixed trading rows that would feed the operator dashboard.
    async with database.session() as session:
        trades = TradeRepository(session)
        positions = PositionRepository(session)
        orders = OrderRepository(session)
        await trades.create(_trade("old-open", TradeState.OPEN, NOW))
        await trades.create(
            _trade(
                "old-closed-win",
                TradeState.CLOSED,
                NOW - timedelta(minutes=2),
                profit=Decimal("2.50"),
            ),
        )
        await trades.create(
            _trade(
                "old-closed-loss",
                TradeState.CLOSED,
                NOW - timedelta(minutes=1),
                profit=Decimal("-0.75"),
            ),
        )
        await trades.create(_trade("new-closed", TradeState.CLOSED, NOW + timedelta(minutes=2)))
        await positions.create(_position("closed-position", TradeState.CLOSED, NOW))
        await positions.create(
            _position("open-position", TradeState.OPEN, NOW + timedelta(minutes=1)),
        )
        await orders.create(_order("old-order", NOW))
        await orders.create(_order("new-order", NOW + timedelta(minutes=3)))
        await orders.create(
            _order("open-order", NOW + timedelta(minutes=4), state=OrderState.OPEN),
        )
        await session.commit()

    # When: dashboard list methods are called with tight limits.
    async with database.session() as session:
        recent_trades = await TradeRepository(session).list_recent(limit=1)
        open_trades = await TradeRepository(session).list_open(limit=5)
        open_positions = await PositionRepository(session).list_open(limit=5)
        recent_orders = await OrderRepository(session).list_recent(limit=1)
        open_orders = await OrderRepository(session).list_open(limit=5)
        closed_trade_summary = await TradeRepository(session).closed_trade_summary()

    # Then: each list is bounded, ordered newest-first, and filters open state.
    assert tuple(trade.trade_id for trade in recent_trades) == ("new-closed",)
    assert tuple(trade.trade_id for trade in open_trades) == ("old-open",)
    assert tuple(position.position_id for position in open_positions) == ("open-position",)
    assert tuple(order.order_id for order in recent_orders) == ("open-order",)
    assert tuple(order.order_id for order in open_orders) == ("open-order",)
    assert closed_trade_summary.closed_trades == 3
    assert closed_trade_summary.wins == 2
    assert closed_trade_summary.losses == 1
    assert closed_trade_summary.profit == Decimal("2.75")


async def test_lock_repository_returns_active_dashboard_locks(
    database: PersistenceDatabase,
) -> None:
    # Given: active and expired dashboard locks.
    async with database.session() as session:
        locks = LockRepository(session)
        await locks.acquire(_lock("expired", NOW - timedelta(minutes=2)))
        await locks.acquire(_lock("active-later", NOW + timedelta(minutes=5)))
        await locks.acquire(_lock("active-sooner", NOW + timedelta(minutes=1)))
        await session.commit()

    # When: active locks are read at a fixed instant.
    async with database.session() as session:
        active_locks = await LockRepository(session).list_active(now=NOW, limit=5)

    # Then: expired locks are removed and active locks are ordered by expiry.
    assert tuple(lock.name for lock in active_locks) == ("active-sooner", "active-later")


async def test_create_app_dashboard_reads_seeded_persistence_rows(
    database: PersistenceDatabase,
) -> None:
    async with database.session() as session:
        await EquitySnapshotRepository(session).add(
            EquitySnapshotRecord(
                captured_at=NOW,
                equity=Decimal("1000.10"),
                available=Decimal("990.05"),
            ),
        )
        await PositionRepository(session).create(_position("open-position", TradeState.OPEN, NOW))
        await TradeRepository(session).create(
            _trade("closed-trade", TradeState.CLOSED, NOW + timedelta(minutes=1)),
        )
        await TradeRepository(session).create(
            _trade(
                "older-closed-loss",
                TradeState.CLOSED,
                NOW - timedelta(minutes=1),
                profit=Decimal("-0.25"),
            ),
        )
        await session.commit()
    settings = RuntimeSettings(
        database=DatabaseSettings(url=database.database_url),
    )

    async with AsyncClient(
        transport=ASGITransport(
            app=create_app(
                settings=settings,
                dashboard_store=PersistenceDashboardReadStore(database, trade_limit=1),
            ),
        ),
        base_url="http://testserver",
    ) as client:
        snapshot_response = await client.get("/api/v1/dashboard/snapshot")
        home_response = await client.get("/")
    snapshot = DashboardSnapshotResponse.model_validate_json(snapshot_response.content)

    assert snapshot_response.status_code == 200
    assert snapshot.equity_points[0].equity == "1000.10"
    assert snapshot.open_positions[0].position_id == "open-position"
    assert snapshot.recent_trades[0].trade_id == "closed-trade"
    assert len(snapshot.recent_trades) == 1
    assert snapshot.closed_trade_summary.closed_trades == 2
    assert snapshot.closed_trade_summary.wins == 1
    assert snapshot.closed_trade_summary.losses == 1
    assert snapshot.closed_trade_summary.profit == "0.75"
    assert home_response.status_code == 200
    assert 'data-nfi-page="home"' in home_response.text


async def test_persistence_dashboard_store_initializes_database_once(
    database: PersistenceDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initialize_calls = 0
    original_initialize = PersistenceDatabase.initialize

    async def counted_initialize(self: PersistenceDatabase) -> None:
        nonlocal initialize_calls
        initialize_calls += 1
        await original_initialize(self)

    monkeypatch.setattr(PersistenceDatabase, "initialize", counted_initialize)
    store = PersistenceDashboardReadStore(database)

    await store.read_models()
    await store.read_models()

    assert initialize_calls == 1


def _trade(
    trade_id: str,
    state: TradeState,
    opened_at: datetime,
    *,
    profit: Decimal | None = None,
) -> TradeRecord:
    closed_at, exit_price, default_profit = _trade_close_values(state, opened_at)
    return TradeRecord(
        trade_id=trade_id,
        pair="BTC/USDT",
        side=PositionSide.LONG,
        state=state,
        opened_at=opened_at,
        closed_at=closed_at,
        entry_price=Decimal(100),
        exit_price=exit_price,
        quantity=Decimal("0.1"),
        leverage=Decimal(1),
        profit=default_profit if profit is None else profit,
    )


def _trade_close_values(
    state: TradeState,
    opened_at: datetime,
) -> tuple[datetime | None, Decimal | None, Decimal]:
    match state:
        case TradeState.CLOSED:
            return opened_at, Decimal(101), Decimal("1.0")
        case TradeState.PLANNED | TradeState.OPEN | TradeState.HALTED:
            return None, None, Decimal(0)
        case unreachable:
            assert_never(unreachable)


def _position(position_id: str, state: TradeState, updated_at: datetime) -> PositionRecord:
    return PositionRecord(
        position_id=position_id,
        trade_id=position_id.replace("position", "trade"),
        pair="BTC/USDT",
        side=PositionSide.LONG,
        state=state,
        quantity=Decimal("0.1"),
        entry_price=Decimal(100),
        leverage=Decimal(1),
        updated_at=updated_at,
    )


def _order(
    order_id: str,
    created_at: datetime,
    *,
    state: OrderState = OrderState.FILLED,
) -> OrderRecord:
    return OrderRecord(
        order_id=order_id,
        trade_id="trade-for-order",
        pair="BTC/USDT",
        side=PositionSide.LONG,
        order_type=OrderType.MARKET,
        state=state,
        price=Decimal(100),
        quantity=Decimal("0.1"),
        created_at=created_at,
    )


def _lock(name: str, expires_at: datetime) -> LockRecord:
    return LockRecord(
        name=name,
        owner="dashboard-test",
        acquired_at=NOW,
        expires_at=expires_at,
    )
