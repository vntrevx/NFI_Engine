from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum, unique
from typing import ClassVar, Final, assert_never

from pydantic import BaseModel, ConfigDict

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import (
    Leverage,
    OrderState,
    OrderType,
    PositionSide,
    Price,
    Quantity,
    TradingMode,
    TradingPair,
)
from nfi_engine.exchange.models import ExchangeOrder, ExchangeOrderRequest, Tick
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.exchange.testnet_pilot import build_testnet_pilot_report
from nfi_engine.exchange.testnet_pilot_models import TestnetPilotState

DEFAULT_EXECUTION_PRICE: Final = Decimal(100)
DEFAULT_EXECUTION_QUANTITY: Final = Decimal("0.10")
DEFAULT_EXECUTION_LEVERAGE: Final = "3"
DEFAULT_EXECUTION_AT: Final = datetime(2026, 1, 1, tzinfo=UTC)


@unique
class TestnetExecutionEventSource(StrEnum):
    INTENT = "intent"
    RISK = "risk"
    ADAPTER = "adapter"
    RECONCILIATION = "reconciliation"


class TestnetExecutionEvent(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    state: TestnetPilotState
    source: TestnetExecutionEventSource


class TestnetExecutionReport(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    exchange: str
    trading_mode: str
    testnet: bool
    execution_ready: bool
    live_money_orders_enabled: bool
    live_exchange_observed: bool
    client_order_id: str
    submitted_order_id: str | None
    adapter_order_state: OrderState | None
    final_state: TestnetPilotState | None
    events: tuple[TestnetExecutionEvent, ...]
    blockers: tuple[str, ...]


async def run_testnet_execution_dry_run(settings: RuntimeSettings) -> TestnetExecutionReport:
    pilot_report = build_testnet_pilot_report(settings=settings)
    if not pilot_report.pilot_ready:
        return TestnetExecutionReport(
            exchange=pilot_report.exchange,
            trading_mode=pilot_report.trading_mode,
            testnet=pilot_report.testnet,
            execution_ready=False,
            live_money_orders_enabled=False,
            live_exchange_observed=False,
            client_order_id=pilot_report.sample_client_order_id,
            submitted_order_id=None,
            adapter_order_state=None,
            final_state=None,
            events=(
                TestnetExecutionEvent(
                    state=TestnetPilotState.INTENT_CREATED,
                    source=TestnetExecutionEventSource.INTENT,
                ),
            ),
            blockers=pilot_report.blockers,
        )

    pair = _execution_pair(settings.exchange.trading_mode)
    simulator = DeterministicExchangeSimulator(
        ticks=(
            Tick(
                pair=pair,
                price=Price(DEFAULT_EXECUTION_PRICE),
                at=DEFAULT_EXECUTION_AT,
            ),
        ),
    )
    request = ExchangeOrderRequest(
        pair=pair,
        side=PositionSide.LONG,
        order_type=OrderType.MARKET,
        quantity=Quantity(DEFAULT_EXECUTION_QUANTITY),
        price=None,
        leverage=Leverage.parse(DEFAULT_EXECUTION_LEVERAGE),
    )
    submitted_order = await simulator.create_order(request)
    observed_order = await simulator.fetch_order(
        order_id=submitted_order.order_id,
        pair=submitted_order.pair,
    )
    events = testnet_execution_events_for_order(observed_order)
    return TestnetExecutionReport(
        exchange=pilot_report.exchange,
        trading_mode=pilot_report.trading_mode,
        testnet=pilot_report.testnet,
        execution_ready=True,
        live_money_orders_enabled=False,
        live_exchange_observed=observed_order.live_exchange,
        client_order_id=pilot_report.sample_client_order_id,
        submitted_order_id=observed_order.order_id,
        adapter_order_state=observed_order.state,
        final_state=events[-1].state,
        events=events,
        blockers=(),
    )


def testnet_execution_events_for_order(
    order: ExchangeOrder,
) -> tuple[TestnetExecutionEvent, ...]:
    adapter_state = testnet_pilot_state_from_order_state(order.state)
    events = (
        TestnetExecutionEvent(
            state=TestnetPilotState.INTENT_CREATED,
            source=TestnetExecutionEventSource.INTENT,
        ),
        TestnetExecutionEvent(
            state=TestnetPilotState.RISK_CHECKED,
            source=TestnetExecutionEventSource.RISK,
        ),
        TestnetExecutionEvent(
            state=TestnetPilotState.SUBMITTED,
            source=TestnetExecutionEventSource.ADAPTER,
        ),
        TestnetExecutionEvent(
            state=adapter_state,
            source=TestnetExecutionEventSource.ADAPTER,
        ),
    )
    if _requires_reconciliation(adapter_state):
        return (
            *events,
            TestnetExecutionEvent(
                state=TestnetPilotState.RECONCILED,
                source=TestnetExecutionEventSource.RECONCILIATION,
            ),
        )
    return events


def testnet_pilot_state_from_order_state(order_state: OrderState) -> TestnetPilotState:
    match order_state:
        case OrderState.CREATED:
            return TestnetPilotState.SUBMITTED
        case OrderState.OPEN:
            return TestnetPilotState.ACKNOWLEDGED
        case OrderState.PARTIALLY_FILLED:
            return TestnetPilotState.PARTIALLY_FILLED
        case OrderState.FILLED:
            return TestnetPilotState.FILLED
        case OrderState.CANCELED:
            return TestnetPilotState.CANCELED
        case OrderState.REJECTED:
            return TestnetPilotState.REJECTED
        case unreachable:
            assert_never(unreachable)


def _requires_reconciliation(state: TestnetPilotState) -> bool:
    match state:
        case (
            TestnetPilotState.FILLED
            | TestnetPilotState.CANCELED
            | TestnetPilotState.REJECTED
            | TestnetPilotState.EXPIRED
        ):
            return True
        case (
            TestnetPilotState.INTENT_CREATED
            | TestnetPilotState.RISK_CHECKED
            | TestnetPilotState.SUBMITTED
            | TestnetPilotState.ACKNOWLEDGED
            | TestnetPilotState.PARTIALLY_FILLED
            | TestnetPilotState.CANCEL_REQUESTED
            | TestnetPilotState.RECONCILED
        ):
            return False
        case unreachable:
            assert_never(unreachable)


def _execution_pair(trading_mode: TradingMode) -> TradingPair:
    match trading_mode:
        case TradingMode.FUTURES:
            return TradingPair.parse("BTC/USDT:USDT", trading_mode)
        case TradingMode.SPOT:
            return TradingPair.parse("BTC/USDT", trading_mode)
        case unreachable:
            assert_never(unreachable)
