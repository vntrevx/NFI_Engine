from __future__ import annotations

from decimal import Decimal

import pytest

from nfi_engine.domain import TradingMode, TradingPair
from nfi_engine.strategy import (
    DataProviderFacade,
    PairFrame,
    StrategyContractError,
    StrategyErrorCode,
    StrategyFrame,
    StrategyRow,
)


def test_data_provider_facade_returns_visible_rows_only() -> None:
    # Given
    frame = _frame(first_close=Decimal(10), visible_row_count=1)
    provider = DataProviderFacade(
        frames=(PairFrame(pair=_base_pair(), timeframe="5m", frame=frame),),
    )

    # When
    visible = provider.get_pair_dataframe(pair=_base_pair(), timeframe="5m")

    # Then
    assert len(visible.rows) == 1
    assert visible.rows[0].close == Decimal(10)


def test_data_provider_facade_returns_base_informative_timeframe() -> None:
    # Given
    provider = DataProviderFacade(
        frames=(
            PairFrame(pair=_base_pair(), timeframe="5m", frame=_frame(first_close=Decimal(10))),
            PairFrame(pair=_base_pair(), timeframe="1h", frame=_frame(first_close=Decimal(60))),
        ),
    )

    # When
    visible = provider.get_informative_dataframe(pair=_base_pair(), timeframe="1h")

    # Then
    assert visible.rows[0].close == Decimal(60)


def test_data_provider_facade_returns_btc_informative_frame_for_futures_quote() -> None:
    # Given
    provider = DataProviderFacade(
        frames=(
            PairFrame(pair=_base_pair(), timeframe="5m", frame=_frame(first_close=Decimal(10))),
            PairFrame(
                pair=_btc_futures_pair(), timeframe="1h", frame=_frame(first_close=Decimal(100))
            ),
        ),
    )

    # When
    visible = provider.get_btc_informative_dataframe(pair=_base_pair(), timeframe="1h")

    # Then
    assert provider.btc_pair_for(_base_pair()).normalized == "BTC/USDT:USDT"
    assert visible.rows[0].close == Decimal(100)


def test_data_provider_facade_derives_btc_spot_pair_without_settle_asset() -> None:
    # Given
    provider = DataProviderFacade(frames=())

    # When
    btc_pair = provider.btc_pair_for(TradingPair.parse("ETH/USDT", TradingMode.SPOT))

    # Then
    assert btc_pair.normalized == "BTC/USDT"


def test_data_provider_facade_blocks_missing_pair() -> None:
    # Given
    provider = DataProviderFacade(
        frames=(
            PairFrame(pair=_base_pair(), timeframe="5m", frame=_frame(first_close=Decimal(10))),
        ),
    )

    # When
    with pytest.raises(StrategyContractError) as exc_info:
        provider.get_pair_dataframe(pair=_btc_futures_pair(), timeframe="5m")

    # Then
    assert exc_info.value.code is StrategyErrorCode.DATA_PROVIDER_FRAME_NOT_FOUND


def test_data_provider_facade_blocks_missing_timeframe() -> None:
    # Given
    provider = DataProviderFacade(
        frames=(
            PairFrame(
                pair=_btc_futures_pair(), timeframe="1h", frame=_frame(first_close=Decimal(100))
            ),
        ),
    )

    # When
    with pytest.raises(StrategyContractError) as exc_info:
        provider.get_btc_informative_dataframe(pair=_base_pair(), timeframe="4h")

    # Then
    assert exc_info.value.code is StrategyErrorCode.DATA_PROVIDER_FRAME_NOT_FOUND


def test_data_provider_facade_blocks_stale_frame() -> None:
    # Given
    provider = DataProviderFacade(
        frames=(
            PairFrame(
                pair=_btc_futures_pair(),
                timeframe="1h",
                frame=_frame(first_close=Decimal(100)),
                stale=True,
            ),
        ),
    )

    # When
    with pytest.raises(StrategyContractError) as exc_info:
        provider.get_btc_informative_dataframe(pair=_base_pair(), timeframe="1h")

    # Then
    assert exc_info.value.code is StrategyErrorCode.DATA_PROVIDER_FRAME_STALE


def test_data_provider_facade_deduplicates_current_whitelist() -> None:
    # Given
    provider = DataProviderFacade(
        frames=(
            PairFrame(pair=_base_pair(), timeframe="5m", frame=_frame(first_close=Decimal(10))),
            PairFrame(pair=_base_pair(), timeframe="1h", frame=_frame(first_close=Decimal(60))),
            PairFrame(
                pair=_btc_futures_pair(), timeframe="1h", frame=_frame(first_close=Decimal(100))
            ),
        ),
    )

    # When
    whitelist = provider.current_whitelist()

    # Then
    assert whitelist == ("ETH/USDT:USDT", "BTC/USDT:USDT")


def _base_pair() -> TradingPair:
    return TradingPair.parse("ETH/USDT:USDT", TradingMode.FUTURES)


def _btc_futures_pair() -> TradingPair:
    return TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)


def _frame(*, first_close: Decimal, visible_row_count: int = 2) -> StrategyFrame:
    second_close = first_close + Decimal(1)
    return StrategyFrame(
        rows=(
            StrategyRow(date="2026-01-01T00:00:00Z", close=first_close),
            StrategyRow(date="2026-01-01T00:05:00Z", close=second_close),
        ),
        visible_row_count=visible_row_count,
    )
