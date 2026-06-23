from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Final

from nfi_engine.backtest import (
    BacktestRequest,
    ReproducibilityMetadata,
    SimulationSettings,
    result_to_json_payload,
    run_backtest,
)
from nfi_engine.data import CandleBatch
from nfi_engine.domain import (
    Candle,
    PositionSide,
    Price,
    Quantity,
    SignalType,
    TradeId,
    TradingMode,
    TradingPair,
)
from nfi_engine.strategy import (
    FreqtradeStrategyAdapter,
    RunMode,
    SignalColumns,
    StrategyFeature,
    StrategyFeatureName,
    StrategyFrame,
    StrategyMetadata,
    StrategyRow,
    StrategyTrade,
)
from nfi_engine.strategy.nfi_x7 import (
    LONG_EXIT_TAG,
    SHORT_EXIT_TAG,
    X7CustomExitReason,
    X7ExitReason,
    X7NativeStrategy,
    build_x7_custom_exit_decision,
    build_x7_exit_decision,
)

ONE: Final = Decimal(1)
ZERO: Final = Decimal(0)
TEN: Final = Decimal(10)
ONE_THOUSAND: Final = Decimal(1000)
NOOP_SHORT_EXIT_TAG: Final = "unit-exit-short-noop"


def test_x7_exit_decision_marks_long_exit_on_bounded_pullback() -> None:
    # Given
    row = _row_with_features(roc=Decimal("-0.60"), range_pct=Decimal("2.0"))

    # When
    decision = build_x7_exit_decision(row, visible_rows=3)

    # Then
    assert decision.reason is X7ExitReason.LONG_MOMENTUM_COOLDOWN
    assert decision.columns.exit_long is True
    assert decision.columns.exit_tag == LONG_EXIT_TAG


def test_x7_exit_decision_marks_short_exit_on_bounded_rebound() -> None:
    # Given
    row = _row_with_features(roc=Decimal("0.30"), range_pct=Decimal("2.0"))

    # When
    decision = build_x7_exit_decision(row, visible_rows=3)

    # Then
    assert decision.reason is X7ExitReason.SHORT_MOMENTUM_COOLDOWN
    assert decision.columns.exit_short is True
    assert decision.columns.exit_tag == SHORT_EXIT_TAG


def test_x7_exit_decision_keeps_warmup_rows_signal_free() -> None:
    # Given
    row = _row_with_features(roc=Decimal("-0.60"), range_pct=Decimal("2.0"))

    # When
    decision = build_x7_exit_decision(row, visible_rows=1)

    # Then
    assert decision.reason is X7ExitReason.WARMUP
    assert decision.columns.exit_long is False
    assert decision.columns.exit_tag is None


def test_x7_native_strategy_surfaces_exit_reason_through_adapter_signal() -> None:
    # Given
    strategy = X7NativeStrategy()
    adapter = FreqtradeStrategyAdapter.from_strategy(strategy)
    frame = StrategyFrame(
        rows=(
            StrategyRow(date="2026-01-01T00:00:00+00:00", close=Decimal(100)),
            StrategyRow(date="2026-01-01T00:05:00+00:00", close=Decimal(101)),
            StrategyRow(date="2026-01-01T00:10:00+00:00", close=Decimal("100.4")),
        ),
    )

    # When
    signals = adapter.analyze(frame, _metadata(), incremental=True)

    # Then
    assert tuple((signal.side, signal.signal_type, signal.tag) for signal in signals) == (
        (PositionSide.LONG, SignalType.EXIT, LONG_EXIT_TAG),
    )


def test_x7_backtest_closes_long_with_native_exit_reason_and_timeline_reason() -> None:
    # Given
    request = _backtest_request(
        strategy=X7NativeStrategy(),
        closes=(Decimal(100), Decimal(101), Decimal("100.4")),
    )

    # When
    result = run_backtest(request)
    payload = result_to_json_payload(result)

    # Then
    assert result.summary.total_trades == 1
    assert payload["trades"][0]["side"] == "long"
    assert payload["trades"][0]["exit_reason"] == LONG_EXIT_TAG
    assert payload["timeline"]["steps"][2]["exit_signals"] == 1
    assert payload["timeline"]["steps"][2]["exit_reasons"] == [LONG_EXIT_TAG]
    assert payload["timeline"]["steps"][2]["closed_orders"] == 1


def test_backtest_records_noop_reason_when_exit_signal_side_has_no_open_trade() -> None:
    # Given
    request = _backtest_request(
        strategy=OppositeSideExitStrategy(),
        closes=(Decimal(100), Decimal(101), Decimal(102)),
    )

    # When
    result = run_backtest(request)
    payload = result_to_json_payload(result)

    # Then
    assert result.summary.total_trades == 1
    assert payload["trades"][0]["exit_reason"] == "end_of_data"
    assert payload["timeline"]["steps"][1]["exit_sides"] == ["short"]
    assert payload["timeline"]["steps"][1]["exit_reasons"] == [NOOP_SHORT_EXIT_TAG]
    assert payload["timeline"]["steps"][1]["closed_orders"] == 0
    assert payload["timeline"]["steps"][1]["rejected_actions"] == 1
    assert payload["timeline"]["steps"][1]["open_trade_count"] == 1


def test_x7_custom_exit_decision_stays_explicit_when_trade_lacks_feature_context() -> None:
    # Given
    pair = TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
    trade = StrategyTrade(trade_id=TradeId("trade-1"), pair=pair, side=PositionSide.LONG)

    # When
    decision = build_x7_custom_exit_decision(trade)

    # Then
    assert decision.reason is X7CustomExitReason.FEATURE_CONTEXT_REQUIRED
    assert decision.exit_reason is None


class OppositeSideExitStrategy:
    timeframe: str = "5m"
    can_short: bool = True

    def populate_indicators(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        return dataframe

    def populate_entry_trend(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        if dataframe.last_visible_row().date == "2026-01-01T00:00:00+00:00":
            return dataframe.with_signal(index=-1, columns=SignalColumns(enter_long=True))
        return dataframe

    def populate_exit_trend(
        self,
        dataframe: StrategyFrame,
        _metadata: StrategyMetadata,
    ) -> StrategyFrame:
        if dataframe.last_visible_row().date == "2026-01-01T00:05:00+00:00":
            return dataframe.with_signal(
                index=-1,
                columns=SignalColumns(exit_short=True, exit_tag=NOOP_SHORT_EXIT_TAG),
            )
        return dataframe


def _row_with_features(*, roc: Decimal, range_pct: Decimal) -> StrategyRow:
    return StrategyRow(
        date="2026-01-01T00:10:00+00:00",
        close=Decimal(100),
        features=(
            StrategyFeature(name=StrategyFeatureName("x7_base_roc_1"), value=roc),
            StrategyFeature(name=StrategyFeatureName("x7_base_range_pct"), value=range_pct),
        ),
    )


def _backtest_request(
    *,
    strategy: object,
    closes: tuple[Decimal, ...],
) -> BacktestRequest:
    return BacktestRequest(
        candles=_batch_with_closes(closes),
        adapter=FreqtradeStrategyAdapter.from_strategy(strategy),
        settings=_settings(),
        config_digest="x7-exit-unit",
        strategy_name=type(strategy).__name__,
        metadata=_reproducibility_metadata(),
    )


def _batch_with_closes(closes: tuple[Decimal, ...]) -> CandleBatch:
    pair = TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
    opened_at = datetime(2026, 1, 1, tzinfo=UTC)
    candles = tuple(
        Candle(
            pair=pair,
            opened_at=opened_at + timedelta(minutes=index * 5),
            open=Price(close),
            high=Price(close),
            low=Price(close),
            close=Price(close),
            volume=Quantity(ONE),
        )
        for index, close in enumerate(closes)
    )
    return CandleBatch(pair=pair, timeframe="5m", candles=candles)


def _settings() -> SimulationSettings:
    return SimulationSettings(
        trading_mode=TradingMode.FUTURES,
        starting_balance=ONE_THOUSAND,
        stake_amount=TEN,
        fee_rate=ZERO,
        slippage_rate=ZERO,
        max_open_trades=1,
        leverage=ONE,
        liquidation_buffer=Decimal("0.05"),
        stoploss_pct=Decimal("0.10"),
    )


def _reproducibility_metadata() -> ReproducibilityMetadata:
    return ReproducibilityMetadata(
        config_hash="x7-exit-unit",
        strategy_hash="strategy-x7-exit-unit",
        data_hash="data-x7-exit-unit",
        engine_version="0.1.0",
        git_commit=None,
        dependency_lock_hash="lock-x7-exit-unit",
        python_version="3.12.0",
        created_at=datetime(2026, 1, 1, tzinfo=UTC),
        command_args=("backtest", "--config", "x7-exit-unit.yaml"),
    )


def _metadata() -> StrategyMetadata:
    return StrategyMetadata(
        pair=TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES),
        timeframe="5m",
        runmode=RunMode.BACKTEST,
    )
