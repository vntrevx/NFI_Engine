from __future__ import annotations

from typing import assert_never

from nfi_engine.domain import OrderState
from nfi_engine.exchange.models import ExchangeOrder
from nfi_engine.exchange.testnet_execution_models import (
    TestnetExecutionEvent,
    TestnetExecutionEventSource,
)
from nfi_engine.exchange.testnet_pilot_models import TestnetPilotState


def testnet_intent_events() -> tuple[TestnetExecutionEvent, ...]:
    return (
        _execution_event(
            TestnetPilotState.INTENT_CREATED,
            TestnetExecutionEventSource.INTENT,
        ),
    )


def testnet_pre_submission_events() -> tuple[TestnetExecutionEvent, ...]:
    return (
        *testnet_intent_events(),
        _execution_event(
            TestnetPilotState.RISK_CHECKED,
            TestnetExecutionEventSource.RISK,
        ),
    )


def testnet_submission_attempt_events() -> tuple[TestnetExecutionEvent, ...]:
    return (
        *testnet_pre_submission_events(),
        _execution_event(
            TestnetPilotState.SUBMITTED,
            TestnetExecutionEventSource.ADAPTER,
        ),
    )


def testnet_execution_events_for_order(
    order: ExchangeOrder,
) -> tuple[TestnetExecutionEvent, ...]:
    adapter_state = testnet_pilot_state_from_order_state(order.state)
    events = (
        *testnet_submission_attempt_events(),
        _execution_event(
            adapter_state,
            TestnetExecutionEventSource.ADAPTER,
        ),
    )
    if _requires_reconciliation(adapter_state):
        return (
            *events,
            _execution_event(
                TestnetPilotState.RECONCILED,
                TestnetExecutionEventSource.RECONCILIATION,
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


def _execution_event(
    state: TestnetPilotState,
    source: TestnetExecutionEventSource,
) -> TestnetExecutionEvent:
    return TestnetExecutionEvent(state=state, source=source)


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
