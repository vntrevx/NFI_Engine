from __future__ import annotations

from decimal import Decimal

import pytest

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import (
    OrderState,
    OrderType,
    PositionSide,
    Price,
    Quantity,
    TradingMode,
    TradingPair,
)
from nfi_engine.exchange.models import ExchangeOrder
from nfi_engine.exchange.testnet_execution import (
    run_testnet_execution_dry_run,
)
from nfi_engine.exchange.testnet_execution import (
    testnet_execution_events_for_order as build_testnet_execution_events_for_order,
)
from nfi_engine.exchange.testnet_execution import (
    testnet_pilot_state_from_order_state as map_testnet_pilot_state_from_order_state,
)
from nfi_engine.exchange.testnet_pilot_models import TestnetPilotState as PilotState


@pytest.mark.anyio
async def test_testnet_execution_blocks_before_adapter_without_pilot_controls() -> None:
    report = await run_testnet_execution_dry_run(RuntimeSettings())

    assert report.execution_ready is False
    assert report.live_money_orders_enabled is False
    assert report.live_exchange_observed is False
    assert report.submitted_order_id is None
    assert report.adapter_order_state is None
    assert report.final_state is None
    assert report.blockers
    assert tuple(event.state for event in report.events) == (PilotState.INTENT_CREATED,)


@pytest.mark.parametrize(
    ("order_state", "pilot_state"),
    [
        (OrderState.CREATED, PilotState.SUBMITTED),
        (OrderState.OPEN, PilotState.ACKNOWLEDGED),
        (OrderState.PARTIALLY_FILLED, PilotState.PARTIALLY_FILLED),
        (OrderState.FILLED, PilotState.FILLED),
        (OrderState.CANCELED, PilotState.CANCELED),
        (OrderState.REJECTED, PilotState.REJECTED),
    ],
)
def test_testnet_execution_maps_all_domain_order_states(
    order_state: OrderState,
    pilot_state: PilotState,
) -> None:
    assert map_testnet_pilot_state_from_order_state(order_state) is pilot_state


def test_testnet_execution_reconciles_terminal_adapter_order() -> None:
    pair = TradingPair.parse("BTC/USDT:USDT", TradingMode.FUTURES)
    order = ExchangeOrder(
        order_id="sim-1",
        pair=pair,
        side=PositionSide.LONG,
        order_type=OrderType.MARKET,
        state=OrderState.FILLED,
        quantity=Quantity(Decimal("0.10")),
        price=None,
        filled_price=Price(Decimal(100)),
        live_exchange=False,
    )

    events = build_testnet_execution_events_for_order(order)

    assert tuple(event.state for event in events) == (
        PilotState.INTENT_CREATED,
        PilotState.RISK_CHECKED,
        PilotState.SUBMITTED,
        PilotState.FILLED,
        PilotState.RECONCILED,
    )
    assert order.live_exchange is False
