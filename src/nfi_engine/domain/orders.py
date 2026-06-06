from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, assert_never

from nfi_engine.domain.enums import ErrorCode, OrderType, PositionSide, TimeInForce, TradingMode
from nfi_engine.domain.errors import DomainError
from nfi_engine.domain.risk import Leverage

if TYPE_CHECKING:
    from nfi_engine.domain.pairs import TradingPair


@dataclass(frozen=True, slots=True)
class OrderIntent:
    pair: TradingPair
    trading_mode: TradingMode
    side: PositionSide
    order_type: OrderType
    time_in_force: TimeInForce
    leverage: Leverage


@dataclass(frozen=True, slots=True)
class OrderIntentDraft:
    pair: TradingPair
    trading_mode: TradingMode
    side: PositionSide
    order_type: OrderType
    leverage: Leverage | None = None
    time_in_force: TimeInForce = TimeInForce.GTC


def create_order_intent(draft: OrderIntentDraft) -> OrderIntent:
    draft.pair.require_mode(draft.trading_mode)
    _validate_side_for_mode(trading_mode=draft.trading_mode, side=draft.side)
    return OrderIntent(
        pair=draft.pair,
        trading_mode=draft.trading_mode,
        side=draft.side,
        order_type=draft.order_type,
        time_in_force=draft.time_in_force,
        leverage=Leverage.one() if draft.leverage is None else draft.leverage,
    )


def _validate_side_for_mode(*, trading_mode: TradingMode, side: PositionSide) -> None:
    match trading_mode:
        case TradingMode.SPOT:
            match side:
                case PositionSide.LONG:
                    return
                case PositionSide.SHORT:
                    raise DomainError(
                        code=ErrorCode.SPOT_SHORT_NOT_ALLOWED,
                        message="spot trading only supports long order intents",
                    )
                case unreachable:
                    assert_never(unreachable)
        case TradingMode.FUTURES:
            return
        case unreachable:
            assert_never(unreachable)
