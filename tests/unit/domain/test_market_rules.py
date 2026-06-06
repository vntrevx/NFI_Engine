from __future__ import annotations

from decimal import Decimal

import pytest

from nfi_engine.domain import (
    DomainError,
    ErrorCode,
    Leverage,
    LiquidationBuffer,
    OrderIntentDraft,
    OrderType,
    PositionSide,
    TradingMode,
    TradingPair,
    create_order_intent,
)


def test_futures_pair_parses_when_settle_symbol_is_present() -> None:
    # Given
    raw_pair = "ETH/USDT:USDT"

    # When
    pair = TradingPair.parse(raw_pair, TradingMode.FUTURES)

    # Then
    assert pair.base == "ETH"
    assert pair.quote == "USDT"
    assert pair.settle == "USDT"
    assert pair.normalized == raw_pair


def test_malformed_futures_pair_raises_typed_parse_error_when_settle_is_missing() -> None:
    # Given
    raw_pair = "ETH/USDT"

    # When
    with pytest.raises(DomainError) as exc_info:
        TradingPair.parse(raw_pair, TradingMode.FUTURES)

    # Then
    assert exc_info.value.code is ErrorCode.FUTURES_SETTLE_REQUIRED


def test_spot_short_is_rejected_when_order_intent_is_created() -> None:
    # Given
    pair = TradingPair.parse("BTC/USDT", TradingMode.SPOT)

    # When
    with pytest.raises(DomainError) as exc_info:
        create_order_intent(
            OrderIntentDraft(
                pair=pair,
                trading_mode=TradingMode.SPOT,
                side=PositionSide.SHORT,
                order_type=OrderType.MARKET,
            ),
        )

    # Then
    assert exc_info.value.code is ErrorCode.SPOT_SHORT_NOT_ALLOWED


def test_futures_short_is_allowed_when_order_intent_is_created() -> None:
    # Given
    pair = TradingPair.parse("ETH/USDT:USDT", TradingMode.FUTURES)
    leverage = Leverage.parse("3")

    # When
    intent = create_order_intent(
        OrderIntentDraft(
            pair=pair,
            trading_mode=TradingMode.FUTURES,
            side=PositionSide.SHORT,
            order_type=OrderType.MARKET,
            leverage=leverage,
        ),
    )

    # Then
    assert intent.side is PositionSide.SHORT
    assert intent.leverage == leverage


def test_leverage_rejects_values_below_one_when_parsed() -> None:
    # Given
    raw_leverage = "0.5"

    # When
    with pytest.raises(DomainError) as exc_info:
        Leverage.parse(raw_leverage)

    # Then
    assert exc_info.value.code is ErrorCode.LEVERAGE_OUT_OF_RANGE


def test_liquidation_buffer_rejects_values_above_upper_bound_when_parsed() -> None:
    # Given
    raw_buffer = "1.0"

    # When
    with pytest.raises(DomainError) as exc_info:
        LiquidationBuffer.parse(raw_buffer)

    # Then
    assert exc_info.value.code is ErrorCode.LIQUIDATION_BUFFER_OUT_OF_RANGE


def test_liquidation_buffer_accepts_zero_and_documented_default_when_parsed() -> None:
    # Given
    zero = "0.0"
    default = "0.05"

    # When
    zero_buffer = LiquidationBuffer.parse(zero)
    default_buffer = LiquidationBuffer.parse(default)

    # Then
    assert zero_buffer.value == Decimal(zero)
    assert default_buffer.value == Decimal(default)
