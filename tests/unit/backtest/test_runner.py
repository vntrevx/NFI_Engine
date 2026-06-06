from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Final

import pytest

from nfi_engine.backtest import (
    BacktestError,
    BacktestErrorCode,
    BacktestRequest,
    ReproducibilityMetadata,
    SimulationSettings,
    result_to_json_payload,
    run_backtest,
)
from nfi_engine.backtest.config import parse_timerange
from nfi_engine.data import CandleBatch
from nfi_engine.domain import Candle, Price, Quantity, TradingMode, TradingPair
from nfi_engine.strategy import FreqtradeStrategyAdapter, RequiredFreqtradeStrategy
from tests.fixtures.strategies.backtest_cases import (
    EveryCandleLongStrategy,
    LongExitStrategy,
    NoSignalStrategy,
    ShortExitStrategy,
    StoplossLongStrategy,
)

ZERO: Final = Decimal(0)
ONE: Final = Decimal(1)
TWO: Final = Decimal(2)
TEN: Final = Decimal(10)
NINETY: Final = Decimal(90)
NINETY_FIVE: Final = Decimal(95)
ONE_HUNDRED: Final = Decimal(100)
ONE_HUNDRED_FIVE: Final = Decimal(105)
ONE_HUNDRED_TEN: Final = Decimal(110)
ONE_THOUSAND: Final = Decimal(1000)
DEFAULT_PRICES: Final = (ONE_HUNDRED, ONE_HUNDRED_FIVE, ONE_HUNDRED_TEN)
DEFAULT_FEE_RATE: Final = ZERO
DEFAULT_SLIPPAGE_RATE: Final = ZERO
DEFAULT_STOPLOSS: Final = Decimal("0.10")
DEFAULT_LIQUIDATION_BUFFER: Final = Decimal("0.05")


def test_run_backtest_returns_flat_summary_when_strategy_has_no_signal() -> None:
    # Given
    request = _request(strategy=NoSignalStrategy(), settings=_spot_settings())

    # When
    result = run_backtest(request)

    # Then
    assert result.summary.total_trades == 0
    assert result.summary.final_balance == ONE_THOUSAND
    assert len(result.equity_curve) == 3


def test_run_backtest_closes_single_spot_long_when_exit_signal_arrives() -> None:
    # Given
    request = _request(strategy=LongExitStrategy(), settings=_spot_settings())

    # When
    result = run_backtest(request)

    # Then
    assert result.summary.total_trades == 1
    assert result.trades[0].side == "long"
    assert result.trades[0].entry_price == ONE_HUNDRED
    assert result.trades[0].exit_price == ONE_HUNDRED_TEN
    assert result.summary.total_profit == Decimal("1.0")


def test_run_backtest_closes_single_futures_short_when_exit_signal_arrives() -> None:
    # Given
    request = _request(
        strategy=ShortExitStrategy(),
        settings=_futures_settings(leverage=TWO),
        prices=(ONE_HUNDRED, NINETY_FIVE, NINETY),
    )

    # When
    result = run_backtest(request)

    # Then
    assert result.summary.total_trades == 1
    assert result.trades[0].side == "short"
    assert result.trades[0].leverage == TWO
    assert result.summary.total_profit == Decimal("2.0")


def test_run_backtest_closes_long_at_stoploss_when_low_crosses_threshold() -> None:
    # Given
    request = _request(
        strategy=StoplossLongStrategy(),
        settings=_spot_settings(stoploss_pct=Decimal("0.05")),
        prices=(ONE_HUNDRED, Decimal(94), NINETY),
    )

    # When
    result = run_backtest(request)

    # Then
    assert result.summary.total_trades == 1
    assert result.trades[0].exit_reason == "stoploss"
    assert result.trades[0].exit_price == Decimal("95.00")
    assert result.summary.total_profit == Decimal("-0.500")


def test_run_backtest_applies_fee_and_slippage_to_trade_profit() -> None:
    # Given
    clean_result = run_backtest(_request(strategy=LongExitStrategy(), settings=_spot_settings()))
    costed_result = run_backtest(
        _request(
            strategy=LongExitStrategy(),
            settings=_spot_settings(
                fee_rate=Decimal("0.001"),
                slippage_rate=Decimal("0.01"),
            ),
        ),
    )

    # When
    clean_profit = clean_result.summary.total_profit
    costed_trade = costed_result.trades[0]

    # Then
    assert costed_trade.entry_price == Decimal("101.00")
    assert costed_trade.exit_price == Decimal("108.90")
    assert costed_trade.fees > ZERO
    assert costed_result.summary.total_profit < clean_profit


def test_run_backtest_respects_max_open_trades_when_limit_is_zero() -> None:
    # Given
    request = _request(
        strategy=EveryCandleLongStrategy(),
        settings=_spot_settings(max_open_trades=0),
    )

    # When
    result = run_backtest(request)

    # Then
    assert result.summary.total_trades == 0
    assert result.summary.rejected_entries == 3


def test_run_backtest_rejects_futures_stoploss_inside_liquidation_buffer() -> None:
    # Given
    request = _request(
        strategy=ShortExitStrategy(),
        settings=_futures_settings(
            leverage=Decimal(20),
            liquidation_buffer=Decimal("0.03"),
            stoploss_pct=Decimal("0.10"),
        ),
    )

    # When
    with pytest.raises(BacktestError) as exc_info:
        run_backtest(request)

    # Then
    assert exc_info.value.code is BacktestErrorCode.LIQUIDATION_BUFFER_VIOLATION


def test_result_to_json_payload_includes_required_schema_sections() -> None:
    # Given
    result = run_backtest(_request(strategy=LongExitStrategy(), settings=_spot_settings()))

    # When
    payload = result_to_json_payload(result)

    # Then
    assert "trades" in payload
    assert "equity_curve" in payload
    assert "summary" in payload
    assert payload["config_digest"] == "unit-digest"
    assert payload["strategy"]["name"] == "LongExitStrategy"
    assert payload["metadata"]["config_hash"] == "unit-digest"
    assert payload["metadata"]["strategy_hash"] == "strategy-unit-hash"
    assert payload["metadata"]["data_hash"] == "data-unit-hash"
    assert payload["metadata"]["engine_version"] == "0.1.0"
    assert payload["metadata"]["dependency_lock_hash"] == "lock-unit-hash"
    assert payload["metadata"]["created_at"] == "2026-01-01T00:00:00+00:00"


def test_parse_timerange_raises_typed_error_when_input_is_malformed() -> None:
    # Given
    raw_timerange = "not-a-date"

    # When
    with pytest.raises(BacktestError) as exc_info:
        parse_timerange(raw_timerange)

    # Then
    assert exc_info.value.code is BacktestErrorCode.BACKTEST_TIMERANGE_INVALID


def _request(
    *,
    strategy: RequiredFreqtradeStrategy,
    settings: SimulationSettings,
    prices: tuple[Decimal, Decimal, Decimal] = DEFAULT_PRICES,
) -> BacktestRequest:
    trading_mode = settings.trading_mode
    pair = TradingPair.parse(
        "BTC/USDT:USDT" if trading_mode is TradingMode.FUTURES else "BTC/USDT",
        trading_mode,
    )
    return BacktestRequest(
        candles=_batch(pair=pair, prices=prices),
        adapter=FreqtradeStrategyAdapter.from_strategy(strategy),
        settings=settings,
        config_digest="unit-digest",
        strategy_name=type(strategy).__name__,
        metadata=_metadata(),
    )


def _batch(*, pair: TradingPair, prices: tuple[Decimal, Decimal, Decimal]) -> CandleBatch:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    candles = tuple(
        Candle(
            pair=pair,
            opened_at=start + timedelta(minutes=index * 5),
            open=Price(price),
            high=Price(price),
            low=Price(price),
            close=Price(price),
            volume=Quantity(ONE),
        )
        for index, price in enumerate(prices)
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


def _spot_settings(
    *,
    fee_rate: Decimal = DEFAULT_FEE_RATE,
    slippage_rate: Decimal = DEFAULT_SLIPPAGE_RATE,
    max_open_trades: int = 1,
    stoploss_pct: Decimal = DEFAULT_STOPLOSS,
) -> SimulationSettings:
    return SimulationSettings(
        trading_mode=TradingMode.SPOT,
        starting_balance=ONE_THOUSAND,
        stake_amount=TEN,
        fee_rate=fee_rate,
        slippage_rate=slippage_rate,
        max_open_trades=max_open_trades,
        leverage=ONE,
        liquidation_buffer=DEFAULT_LIQUIDATION_BUFFER,
        stoploss_pct=stoploss_pct,
    )


def _futures_settings(
    *,
    leverage: Decimal,
    liquidation_buffer: Decimal = DEFAULT_LIQUIDATION_BUFFER,
    stoploss_pct: Decimal = DEFAULT_STOPLOSS,
) -> SimulationSettings:
    return SimulationSettings(
        trading_mode=TradingMode.FUTURES,
        starting_balance=ONE_THOUSAND,
        stake_amount=TEN,
        fee_rate=ZERO,
        slippage_rate=ZERO,
        max_open_trades=1,
        leverage=leverage,
        liquidation_buffer=liquidation_buffer,
        stoploss_pct=stoploss_pct,
    )
