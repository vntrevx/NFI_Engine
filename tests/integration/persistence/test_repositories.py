from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Final

import pytest

from nfi_engine.domain import OrderState, OrderType, PositionSide, TradeState
from nfi_engine.persistence import create_persistence_database, protocols
from nfi_engine.persistence.records import (
    EquitySnapshotRecord,
    LockRecord,
    OrderRecord,
    PositionRecord,
    StrategyCustomDataRecord,
    TradeRecord,
)
from nfi_engine.persistence.repositories import (
    BotStateRepository,
    EquitySnapshotRepository,
    LockRepository,
    OrderRepository,
    PositionRepository,
    StrategyCustomDataRepository,
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
    db_path = tmp_path / "engine.sqlite"
    database = create_persistence_database(f"sqlite+aiosqlite:///{db_path}")
    await database.initialize()
    try:
        yield database
    finally:
        await database.dispose()


async def test_trade_repository_creates_reads_and_updates_trade(
    database: PersistenceDatabase,
) -> None:
    # Given
    trade = _trade("trade-1")

    # When
    async with database.session() as session:
        repository = TradeRepository(session)
        await repository.create(trade)
        await session.commit()
    async with database.session() as session:
        repository = TradeRepository(session)
        loaded = await repository.get("trade-1")
        await repository.update_state(
            "trade-1",
            TradeState.CLOSED,
            closed_at=NOW + timedelta(minutes=5),
            exit_price=Decimal(111),
            profit=Decimal("1.1"),
        )
        await session.commit()
    async with database.session() as session:
        updated = await TradeRepository(session).get("trade-1")

    # Then
    assert loaded == trade
    assert updated is not None
    assert updated.state is TradeState.CLOSED
    assert updated.exit_price == Decimal(111)
    assert updated.profit == Decimal("1.1")


async def test_order_and_position_repositories_update_state(
    database: PersistenceDatabase,
) -> None:
    # Given
    order = _order("order-1", "trade-2")
    position = _position("position-1", "trade-2")

    # When
    async with database.session() as session:
        order_repository = OrderRepository(session)
        position_repository = PositionRepository(session)
        await order_repository.create(order)
        await order_repository.update_state("order-1", OrderState.FILLED)
        await position_repository.create(position)
        await position_repository.update_state("position-1", TradeState.CLOSED)
        await session.commit()
    async with database.session() as session:
        loaded_order = await OrderRepository(session).get("order-1")
        loaded_position = await PositionRepository(session).get("position-1")

    # Then
    assert loaded_order is not None
    assert loaded_order.state is OrderState.FILLED
    assert loaded_position is not None
    assert loaded_position.state is TradeState.CLOSED


async def test_lock_equity_snapshot_custom_data_and_bot_state_roundtrip(
    database: PersistenceDatabase,
) -> None:
    # Given
    lock = LockRecord(
        name="bot-loop",
        owner="worker-a",
        acquired_at=NOW,
        expires_at=NOW + timedelta(seconds=30),
    )
    snapshot = EquitySnapshotRecord(captured_at=NOW, equity=Decimal(1001), available=Decimal(990))
    custom_data = StrategyCustomDataRecord(
        strategy_name="NFI",
        key="last_signal",
        value_json='{"pair":"BTC/USDT"}',
        updated_at=NOW,
    )

    # When
    async with database.session() as session:
        await LockRepository(session).acquire(lock)
        await EquitySnapshotRepository(session).add(snapshot)
        await StrategyCustomDataRepository(session).put(custom_data)
        await BotStateRepository(session).set("mode", '"paper"')
        await session.commit()
    async with database.session() as session:
        loaded_lock = await LockRepository(session).get("bot-loop")
        snapshots = await EquitySnapshotRepository(session).list_recent(limit=5)
        loaded_custom = await StrategyCustomDataRepository(session).get("NFI", "last_signal")
        bot_state = await BotStateRepository(session).get("mode")

    # Then
    assert loaded_lock == lock
    assert snapshots == (snapshot,)
    assert loaded_custom == custom_data
    assert bot_state == '"paper"'


async def test_transaction_rollback_discards_uncommitted_trade(
    database: PersistenceDatabase,
) -> None:
    # Given
    trade = _trade("rollback-trade")

    # When
    with pytest.raises(RuntimeError, match="rollback"):
        await _create_trade_then_fail(database, trade)
    async with database.session() as session:
        loaded = await TradeRepository(session).get("rollback-trade")

    # Then
    assert loaded is None


async def test_repository_protocols_are_the_public_domain_boundary() -> None:
    # Given
    names = set(protocols.__all__)

    # Then
    assert "TradeRepositoryProtocol" in names
    assert "OrderRepositoryProtocol" in names
    assert "PositionRepositoryProtocol" in names
    assert "LockRepositoryProtocol" in names
    assert "EquitySnapshotRepositoryProtocol" in names
    assert "StrategyCustomDataRepositoryProtocol" in names


async def _create_trade_then_fail(database: PersistenceDatabase, trade: TradeRecord) -> None:
    async with database.session() as session, session.begin():
        await TradeRepository(session).create(trade)
        message = "rollback"
        raise RuntimeError(message)


def _trade(trade_id: str) -> TradeRecord:
    return TradeRecord(
        trade_id=trade_id,
        pair="BTC/USDT",
        side=PositionSide.LONG,
        state=TradeState.OPEN,
        opened_at=NOW,
        closed_at=None,
        entry_price=Decimal(100),
        exit_price=None,
        quantity=Decimal("0.1"),
        leverage=Decimal(1),
        profit=Decimal(0),
    )


def _order(order_id: str, trade_id: str) -> OrderRecord:
    return OrderRecord(
        order_id=order_id,
        trade_id=trade_id,
        pair="BTC/USDT",
        side=PositionSide.LONG,
        order_type=OrderType.MARKET,
        state=OrderState.CREATED,
        price=Decimal(100),
        quantity=Decimal("0.1"),
        created_at=NOW,
    )


def _position(position_id: str, trade_id: str) -> PositionRecord:
    return PositionRecord(
        position_id=position_id,
        trade_id=trade_id,
        pair="BTC/USDT",
        side=PositionSide.LONG,
        state=TradeState.OPEN,
        quantity=Decimal("0.1"),
        entry_price=Decimal(100),
        leverage=Decimal(1),
        updated_at=NOW,
    )
