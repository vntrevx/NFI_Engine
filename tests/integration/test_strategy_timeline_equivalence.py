from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Final

import pytest

from nfi_engine.backtest import (
    BacktestRequest,
    ReproducibilityMetadata,
    SimulationSettings,
    run_backtest,
)
from nfi_engine.config import load_runtime_settings
from nfi_engine.data import CandleBatch
from nfi_engine.domain import Candle, PositionSide, Price, Quantity, TradingMode, TradingPair
from nfi_engine.paper import PaperRunRequest, PaperTick, run_paper
from nfi_engine.strategy import (
    FreqtradeStrategyAdapter,
    SignalColumns,
    StrategyFrame,
    StrategyMetadata,
    StrategyTimeline,
)

pytestmark = pytest.mark.anyio

NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)
ONE: Final = Decimal(1)
TEN: Final = Decimal(10)
ONE_HUNDRED: Final = Decimal(100)
ONE_HUNDRED_FIVE: Final = Decimal(105)
ONE_HUNDRED_TEN: Final = Decimal(110)
ONE_THOUSAND: Final = Decimal(1000)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_backtest_and_paper_share_clean_room_signal_timeline(tmp_path: Path) -> None:
    # Given
    backtest_result = run_backtest(_backtest_request())
    paper_result = await run_paper(_paper_request(tmp_path, timeline=backtest_result.timeline))

    # When
    backtest_entries = sum(step.opened_orders for step in backtest_result.timeline.steps)
    paper_entries = sum(step.opened_orders for step in paper_result.timeline.steps)
    backtest_blocks = sum(step.blocked_actions for step in backtest_result.timeline.steps)
    paper_blocks = sum(step.blocked_actions for step in paper_result.timeline.steps)
    backtest_first = backtest_result.timeline.steps[0]
    paper_first = paper_result.timeline.steps[0]

    # Then
    assert backtest_result.summary.total_trades == paper_result.created_trades == 1
    assert backtest_entries == paper_entries == 1
    assert backtest_blocks == paper_blocks == 0
    assert backtest_first.at == paper_first.at
    assert backtest_first.entry_signals == paper_first.entry_signals
    assert backtest_first.entry_sides == paper_first.entry_sides


def _backtest_request() -> BacktestRequest:
    pair = TradingPair.parse("BTC/USDT", TradingMode.SPOT)
    return BacktestRequest(
        candles=_batch(pair=pair),
        adapter=FreqtradeStrategyAdapter.from_strategy(_EquivalenceLongStrategy()),
        settings=SimulationSettings(
            trading_mode=TradingMode.SPOT,
            starting_balance=ONE_THOUSAND,
            stake_amount=TEN,
            fee_rate=Decimal(0),
            slippage_rate=Decimal(0),
            max_open_trades=1,
            leverage=ONE,
            liquidation_buffer=Decimal("0.05"),
            stoploss_pct=Decimal("0.10"),
        ),
        config_digest="integration-digest",
        strategy_name="LongExitStrategy",
        metadata=ReproducibilityMetadata(
            config_hash="integration-digest",
            strategy_hash="clean-room-long-exit",
            data_hash="three-candle-fixture",
            engine_version="0.1.0",
            git_commit=None,
            dependency_lock_hash="integration-lock",
            python_version="3.12.0",
            created_at=NOW,
            command_args=("integration", "timeline-equivalence"),
        ),
    )


class _EquivalenceLongStrategy:
    timeframe: str = "5m"
    can_short: bool = False

    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        if metadata.timeframe != self.timeframe:
            return dataframe
        return dataframe

    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        if metadata.timeframe != self.timeframe:
            return dataframe
        if dataframe.last_visible_row().date == NOW.isoformat():
            return dataframe.with_signal(
                index=-1,
                columns=SignalColumns(enter_long=True, enter_tag="integration-long"),
            )
        return dataframe

    def populate_exit_trend(
        self,
        dataframe: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> StrategyFrame:
        if metadata.timeframe != self.timeframe:
            return dataframe
        exit_at = (NOW + timedelta(minutes=10)).isoformat()
        if dataframe.last_visible_row().date == exit_at:
            return dataframe.with_signal(index=-1, columns=SignalColumns(exit_long=True))
        return dataframe


def _batch(*, pair: TradingPair) -> CandleBatch:
    prices = (ONE_HUNDRED, ONE_HUNDRED_FIVE, ONE_HUNDRED_TEN)
    candles = tuple(
        Candle(
            pair=pair,
            opened_at=NOW + timedelta(minutes=index * 5),
            open=Price(price),
            high=Price(price),
            low=Price(price),
            close=Price(price),
            volume=Quantity(ONE),
        )
        for index, price in enumerate(prices)
    )
    return CandleBatch(pair=pair, timeframe="5m", candles=candles)


def _paper_request(tmp_path: Path, *, timeline: StrategyTimeline) -> PaperRunRequest:
    pair = TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
    ticks = (
        PaperTick(
            pair=pair,
            at=NOW,
            price=Price(ONE_HUNDRED),
            signal_side=_first_entry_side(timeline),
        ),
        PaperTick(
            pair=pair,
            at=NOW + timedelta(minutes=5),
            price=Price(ONE_HUNDRED_FIVE),
            signal_side=None,
        ),
        PaperTick(
            pair=pair,
            at=NOW + timedelta(minutes=10),
            price=Price(ONE_HUNDRED_TEN),
            signal_side=None,
        ),
    )
    return PaperRunRequest(
        settings=load_runtime_settings(Path("examples/futures-paper.yaml")),
        ticks=ticks,
        max_events=3,
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'paper.sqlite'}",
    )


def _first_entry_side(timeline: StrategyTimeline) -> PositionSide | None:
    for step in timeline.steps:
        if len(step.entry_sides) > 0:
            return step.entry_sides[0]
    return None
