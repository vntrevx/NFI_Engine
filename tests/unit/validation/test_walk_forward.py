from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Final

import pytest

from nfi_engine.backtest import ReproducibilityMetadata, SimulationSettings
from nfi_engine.data import CandleBatch
from nfi_engine.domain import Candle, Price, Quantity, TradingMode, TradingPair
from nfi_engine.strategy import FreqtradeStrategyAdapter
from nfi_engine.validation import (
    ValidationError,
    ValidationErrorCode,
    WalkForwardRequest,
    WalkForwardRole,
    generate_walk_forward_splits,
    run_walk_forward,
)
from tests.fixtures.strategies.backtest_cases import NoSignalStrategy

ONE: Final = Decimal(1)
TEN: Final = Decimal(10)
ONE_HUNDRED: Final = Decimal(100)
ONE_THOUSAND: Final = Decimal(1000)


def test_generate_walk_forward_splits_returns_non_overlapping_roles() -> None:
    # Given: six ordered candles and three requested partitions.
    batch = _batch(candle_count=6)

    # When: walk-forward windows are generated.
    splits = generate_walk_forward_splits(batch, split_count=3)

    # Then: train, validation, and test windows are contiguous and non-overlapping.
    assert tuple(split.role for split in splits) == (
        WalkForwardRole.TRAIN,
        WalkForwardRole.VALIDATION,
        WalkForwardRole.TEST,
    )
    assert tuple(split.candle_count for split in splits) == (2, 2, 2)
    assert splits[0].end <= splits[1].start
    assert splits[1].end <= splits[2].start


def test_generate_walk_forward_splits_rejects_malformed_split_count() -> None:
    # Given: a split count that cannot express train, validation, and test windows.
    batch = _batch(candle_count=6)

    # When/Then: typed validation rejects the request.
    with pytest.raises(ValidationError) as exc_info:
        generate_walk_forward_splits(batch, split_count=2)
    assert exc_info.value.code is ValidationErrorCode.WALK_FORWARD_SPLIT_COUNT_INVALID


def test_run_walk_forward_returns_split_and_aggregate_metrics() -> None:
    # Given: a no-signal strategy and six candles.
    request = WalkForwardRequest(
        candles=_batch(candle_count=6),
        adapter=FreqtradeStrategyAdapter.from_strategy(NoSignalStrategy()),
        settings=_settings(),
        strategy_name="NoSignalStrategy",
        metadata=_metadata(),
        split_count=3,
    )

    # When: walk-forward validation is run.
    result = run_walk_forward(request)

    # Then: each split has metrics and the result makes no profitability claim.
    assert len(result.splits) == 3
    assert result.aggregate_metrics.total_trades == 0
    assert result.profitability_claim is False
    assert result.metadata.config_hash == "config-hash"


def _batch(*, candle_count: int) -> CandleBatch:
    pair = TradingPair.parse("BTC/USDT", TradingMode.SPOT)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    candles = tuple(
        Candle(
            pair=pair,
            opened_at=start + timedelta(minutes=index * 5),
            open=Price(ONE_HUNDRED + index),
            high=Price(ONE_HUNDRED + index),
            low=Price(ONE_HUNDRED + index),
            close=Price(ONE_HUNDRED + index),
            volume=Quantity(ONE),
        )
        for index in range(candle_count)
    )
    return CandleBatch(pair=pair, timeframe="5m", candles=candles)


def _settings() -> SimulationSettings:
    return SimulationSettings(
        trading_mode=TradingMode.SPOT,
        starting_balance=ONE_THOUSAND,
        stake_amount=TEN,
        fee_rate=Decimal(0),
        slippage_rate=Decimal(0),
        max_open_trades=1,
        leverage=ONE,
        liquidation_buffer=Decimal("0.05"),
        stoploss_pct=Decimal("0.10"),
    )


def _metadata() -> ReproducibilityMetadata:
    return ReproducibilityMetadata(
        config_hash="config-hash",
        strategy_hash="strategy-hash",
        data_hash="data-hash",
        engine_version="0.1.0",
        git_commit=None,
        dependency_lock_hash="lock-hash",
        python_version="3.12.0",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        command_args=("validate", "walk-forward"),
    )
