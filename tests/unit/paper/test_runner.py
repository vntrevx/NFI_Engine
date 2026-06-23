from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Final

import pytest

from nfi_engine.config import ExchangeSettings, RuntimeSettings, load_runtime_settings
from nfi_engine.domain import (
    AccountSnapshot,
    MarginMode,
    PositionSide,
    Price,
    StakeAmount,
    TradingMode,
    TradingPair,
)
from nfi_engine.paper import PaperError, PaperRunRequest, PaperTick, run_paper
from nfi_engine.persistence import create_persistence_database
from nfi_engine.persistence.repositories import TradeRepository
from nfi_engine.strategy import TimelineSurface

pytestmark = pytest.mark.anyio

NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_paper_run_respects_max_events(tmp_path: Path) -> None:
    # Given
    request = _request(tmp_path, ticks=_ticks(count=10), max_events=3)

    # When
    result = await run_paper(request)

    # Then
    assert result.processed_events == 3
    assert result.live_orders is False


async def test_paper_run_creates_no_trade_when_ticks_have_no_signals(tmp_path: Path) -> None:
    # Given
    request = _request(tmp_path, ticks=_ticks(count=3), max_events=3)

    # When
    result = await run_paper(request)

    # Then
    assert result.created_trades == 0


async def test_paper_run_persists_long_and_short_signal_trades(tmp_path: Path) -> None:
    # Given
    ticks = (
        _tick(signal_side=PositionSide.LONG),
        _tick(signal_side=PositionSide.SHORT, offset=1),
    )
    request = _request(tmp_path, ticks=ticks, max_events=5)

    # When
    result = await run_paper(request)

    # Then
    assert result.created_trades == 2
    database = create_persistence_database(request.database_url)
    try:
        async with database.session() as session:
            long_trade = await TradeRepository(session).get("paper-1")
            short_trade = await TradeRepository(session).get("paper-2")
    finally:
        await database.dispose()
    assert long_trade is not None
    assert short_trade is not None
    assert long_trade.side is PositionSide.LONG
    assert short_trade.side is PositionSide.SHORT


async def test_paper_run_records_compact_signal_timeline(tmp_path: Path) -> None:
    # Given
    ticks = (
        _tick(signal_side=PositionSide.LONG),
        _tick(offset=1),
        _tick(signal_side=PositionSide.SHORT, offset=2),
    )
    request = _request(tmp_path, ticks=ticks, max_events=5)

    # When
    result = await run_paper(request)

    # Then
    timeline = result.timeline
    assert timeline.surface is TimelineSurface.PAPER
    assert timeline.truncated is False
    assert len(timeline.steps) == 3
    assert timeline.steps[0].indicator_runs == 0
    assert timeline.steps[0].entry_signals == 1
    assert timeline.steps[0].entry_sides == (PositionSide.LONG,)
    assert timeline.steps[0].opened_orders == 1
    assert timeline.steps[0].rejected_actions == 0
    assert timeline.steps[0].stake_amount == Decimal(10)
    assert timeline.steps[0].leverage == Decimal(2)
    assert timeline.steps[1].entry_signals == 0
    assert timeline.steps[2].entry_signals == 1
    assert timeline.steps[2].entry_sides == (PositionSide.SHORT,)
    assert timeline.steps[2].opened_orders == 1


async def test_paper_run_rejects_entry_when_wallet_available_is_below_stake(
    tmp_path: Path,
) -> None:
    # Given
    request = PaperRunRequest(
        settings=load_runtime_settings(Path("examples/futures-paper.yaml")),
        ticks=(_tick(signal_side=PositionSide.LONG),),
        max_events=1,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'paper.sqlite'}",
        account_snapshot=AccountSnapshot(
            captured_at=NOW,
            equity=StakeAmount(Decimal(1000)),
            available=StakeAmount(Decimal(0)),
            positions=(),
        ),
    )

    # When
    result = await run_paper(request)

    # Then
    assert result.created_trades == 0
    assert result.timeline.steps[0].entry_signals == 1
    assert result.timeline.steps[0].opened_orders == 0
    assert result.timeline.steps[0].rejected_actions == 1


async def test_paper_run_rejects_live_exchange_config(tmp_path: Path) -> None:
    # Given
    settings = load_runtime_settings(Path("tests/fixtures/config/bybit-live-denied.yaml"))
    request = PaperRunRequest(
        settings=settings,
        ticks=_ticks(count=1),
        max_events=1,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'paper.sqlite'}",
    )

    # When
    with pytest.raises(PaperError, match="LIVE_EXCHANGE_DISABLED_FOR_MILESTONE"):
        await run_paper(request)


async def test_paper_run_rejects_non_testnet_registry_exchange(tmp_path: Path) -> None:
    # Given: a registry-known exchange configured outside testnet mode.
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="binance",
            trading_mode=TradingMode.FUTURES,
            margin_mode=MarginMode.ISOLATED,
            testnet=False,
        ),
    )
    request = PaperRunRequest(
        settings=settings,
        ticks=_ticks(count=1),
        max_events=1,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'paper.sqlite'}",
    )

    # When/Then: paper mode rejects every non-simulator live exchange.
    with pytest.raises(PaperError, match="LIVE_EXCHANGE_DISABLED_FOR_MILESTONE"):
        await run_paper(request)


def _request(
    tmp_path: Path,
    *,
    ticks: tuple[PaperTick, ...],
    max_events: int,
) -> PaperRunRequest:
    return PaperRunRequest(
        settings=load_runtime_settings(Path("examples/futures-paper.yaml")),
        ticks=ticks,
        max_events=max_events,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'paper.sqlite'}",
    )


def _ticks(*, count: int) -> tuple[PaperTick, ...]:
    return tuple(_tick(offset=index) for index in range(count))


def _tick(*, signal_side: PositionSide | None = None, offset: int = 0) -> PaperTick:
    return PaperTick(
        pair=TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
        at=NOW + timedelta(minutes=offset),
        price=Price(Decimal(100 + offset)),
        signal_side=signal_side,
    )
