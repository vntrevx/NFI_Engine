from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING, Final

from nfi_engine.backtest import (
    BacktestRequest,
    ReproducibilityMetadata,
    SimulationSettings,
    frames,
    run_backtest,
)
from nfi_engine.data import CandleBatch
from nfi_engine.domain import Candle, Price, Quantity, TradingMode, TradingPair
from nfi_engine.strategy import FreqtradeStrategyAdapter, StrategyRow
from tests.fixtures.strategies.backtest_cases import NoSignalStrategy

if TYPE_CHECKING:
    import pytest

CANDLE_COUNT: Final = 64
ONE: Final = Decimal(1)
ONE_HUNDRED: Final = Decimal(100)
ONE_THOUSAND: Final = Decimal(1000)


def test_run_backtest_builds_strategy_rows_once_per_candle(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    row_builds = 0
    original_rows_for_batch = frames.strategy_rows_for_batch

    def counted_rows_for_batch(*, batch: CandleBatch) -> tuple[StrategyRow, ...]:
        nonlocal row_builds
        rows = original_rows_for_batch(batch=batch)
        row_builds += len(rows)
        return rows

    monkeypatch.setattr(frames, "strategy_rows_for_batch", counted_rows_for_batch)

    result = run_backtest(_request(candle_count=CANDLE_COUNT))

    assert len(result.equity_curve) == CANDLE_COUNT
    assert row_builds <= CANDLE_COUNT


def _request(*, candle_count: int) -> BacktestRequest:
    strategy = NoSignalStrategy()
    return BacktestRequest(
        candles=_batch(candle_count=candle_count),
        adapter=FreqtradeStrategyAdapter.from_strategy(strategy),
        settings=SimulationSettings(
            trading_mode=TradingMode.SPOT,
            starting_balance=ONE_THOUSAND,
            stake_amount=Decimal(10),
            fee_rate=Decimal(0),
            slippage_rate=Decimal(0),
            max_open_trades=1,
            leverage=ONE,
            liquidation_buffer=Decimal("0.05"),
            stoploss_pct=Decimal("0.10"),
        ),
        config_digest="unit-digest",
        strategy_name=type(strategy).__name__,
        metadata=_metadata(),
    )


def _batch(*, candle_count: int) -> CandleBatch:
    pair = TradingPair.parse("BTC/USDT", TradingMode.SPOT)
    started_at = datetime(2026, 1, 1, tzinfo=UTC)
    candles = tuple(
        Candle(
            pair=pair,
            opened_at=started_at + timedelta(minutes=index * 5),
            open=Price(ONE_HUNDRED),
            high=Price(ONE_HUNDRED),
            low=Price(ONE_HUNDRED),
            close=Price(ONE_HUNDRED),
            volume=Quantity(ONE),
        )
        for index in range(candle_count)
    )
    return CandleBatch(pair=pair, timeframe="5m", candles=candles)


def _metadata() -> ReproducibilityMetadata:
    return ReproducibilityMetadata(
        config_hash="unit-digest",
        strategy_hash="strategy-unit-hash",
        data_hash="data-unit-hash",
        engine_version="0.1.0",
        git_commit=None,
        dependency_lock_hash="lock-unit-hash",
        python_version="3.12.0",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        command_args=("backtest", "--config", "unit.yaml"),
    )
