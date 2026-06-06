from __future__ import annotations

from decimal import Decimal

import pytest

from nfi_engine.domain import Leverage, PositionSide, SignalType, TradingMode, TradingPair
from nfi_engine.strategy import (
    DataProviderFacade,
    FreqtradeStrategyAdapter,
    NativeStrategy,
    PairFrame,
    RunMode,
    StrategyContractError,
    StrategyErrorCode,
    StrategyFrame,
    StrategyMetadata,
    StrategyRow,
    StrategySignal,
    load_freqtrade_strategy,
)
from tests.fixtures.strategies.invalid import MissingEntryStrategy
from tests.fixtures.strategies.nfi_shape import (
    LookaheadStrategy,
    MetadataLookupStrategy,
    NFISmokeStrategy,
)


def test_native_strategy_protocol_emits_signal_when_implemented() -> None:
    # Given
    metadata = _metadata()
    frame = _frame()
    strategy: NativeStrategy = NativeSmokeStrategy()

    # When
    signals = strategy.analyze(frame, metadata)

    # Then
    assert signals == (
        StrategySignal(
            pair=metadata.pair,
            side=PositionSide.LONG,
            signal_type=SignalType.ENTER,
            tag="native",
        ),
    )


def test_freqtrade_adapter_emits_typed_signals_from_signal_columns() -> None:
    # Given
    adapter = FreqtradeStrategyAdapter.from_strategy(NFISmokeStrategy())

    # When
    signals = adapter.analyze(_frame(), _metadata(), incremental=False)

    # Then
    assert (PositionSide.LONG, SignalType.ENTER, "nfi-smoke") in _signal_view(signals)
    assert (PositionSide.SHORT, SignalType.ENTER, "nfi-smoke") in _signal_view(signals)
    assert (PositionSide.LONG, SignalType.EXIT, None) in _signal_view(signals)
    assert (PositionSide.SHORT, SignalType.EXIT, None) in _signal_view(signals)


def test_freqtrade_adapter_supports_mapping_style_metadata_lookup() -> None:
    # Given
    adapter = FreqtradeStrategyAdapter.from_strategy(MetadataLookupStrategy())

    # When
    signals = adapter.analyze(_frame(), _metadata(), incremental=False)

    # Then
    assert signals == (
        StrategySignal(
            pair=_metadata().pair,
            side=PositionSide.LONG,
            signal_type=SignalType.ENTER,
            tag="5m",
        ),
    )


def test_optional_callbacks_are_reported_when_missing() -> None:
    # Given
    adapter = FreqtradeStrategyAdapter.from_strategy(NFISmokeStrategy())

    # When
    inspection = adapter.inspect()

    # Then
    assert "informative_pairs" in inspection.detected_callbacks
    assert "adjust_trade_position" not in inspection.detected_callbacks


def test_leverage_callback_returns_typed_leverage_when_present() -> None:
    # Given
    adapter = FreqtradeStrategyAdapter.from_strategy(NFISmokeStrategy())

    # When
    leverage = adapter.leverage(_metadata().pair, Leverage.one())

    # Then
    assert leverage.value == Decimal(3)


def test_builtin_demo_strategy_spec_imports_from_default_config_shape() -> None:
    # Given
    strategy_spec = "nfi_engine.strategy.demo:AdapterSmokeStrategy"

    # When
    strategy = load_freqtrade_strategy(strategy_spec)

    # Then
    assert FreqtradeStrategyAdapter.from_strategy(strategy).inspect().name == "AdapterSmokeStrategy"


def test_data_provider_facade_returns_visible_rows_only() -> None:
    # Given
    frame = _frame(visible_row_count=1)
    provider = DataProviderFacade(
        frames=(PairFrame(pair=_metadata().pair, timeframe="5m", frame=frame),),
    )

    # When
    visible = provider.get_pair_dataframe(pair=_metadata().pair, timeframe="5m")

    # Then
    assert len(visible.rows) == 1
    assert visible.rows[0].close == Decimal(10)


def test_missing_required_freqtrade_method_is_rejected() -> None:
    # Given
    strategy = MissingEntryStrategy()

    # When
    with pytest.raises(StrategyContractError) as exc_info:
        FreqtradeStrategyAdapter.from_strategy(strategy)

    # Then
    assert exc_info.value.code is StrategyErrorCode.STRATEGY_CONTRACT_ERROR


def test_incremental_adapter_rejects_future_row_access() -> None:
    # Given
    adapter = FreqtradeStrategyAdapter.from_strategy(LookaheadStrategy())

    # When
    with pytest.raises(StrategyContractError) as exc_info:
        adapter.analyze(_frame(visible_row_count=1), _metadata(), incremental=True)

    # Then
    assert exc_info.value.code is StrategyErrorCode.LOOKAHEAD_ACCESS


class NativeSmokeStrategy:
    def analyze(
        self,
        frame: StrategyFrame,
        metadata: StrategyMetadata,
    ) -> tuple[StrategySignal, ...]:
        if len(frame.rows) == 0:
            return ()
        return (
            StrategySignal(
                pair=metadata.pair,
                side=PositionSide.LONG,
                signal_type=SignalType.ENTER,
                tag="native",
            ),
        )


def _metadata() -> StrategyMetadata:
    return StrategyMetadata(
        pair=TradingPair.parse("ETH/USDT:USDT", TradingMode.FUTURES),
        timeframe="5m",
        runmode=RunMode.BACKTEST,
    )


def _frame(*, visible_row_count: int = 2) -> StrategyFrame:
    return StrategyFrame(
        rows=(
            StrategyRow(date="2026-01-01T00:00:00Z", close=Decimal(10)),
            StrategyRow(date="2026-01-01T00:05:00Z", close=Decimal(11)),
        ),
        visible_row_count=visible_row_count,
    )


def _signal_view(
    signals: tuple[StrategySignal, ...],
) -> tuple[tuple[PositionSide, SignalType, str | None], ...]:
    return tuple((signal.side, signal.signal_type, signal.tag) for signal in signals)
