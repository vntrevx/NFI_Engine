from __future__ import annotations

from enum import StrEnum, unique
from typing import Final


@unique
class ExecutionState(StrEnum):
    INTENT_CREATED = "intent_created"
    RISK_CHECKED = "risk_checked"
    SUBMITTED = "submitted"
    ACKNOWLEDGED = "acknowledged"
    PARTIALLY_FILLED = "partially_filled"
    FILLED = "filled"
    CANCEL_REQUESTED = "cancel_requested"
    CANCELED = "canceled"
    REJECTED = "rejected"
    EXPIRED = "expired"
    RECONCILED = "reconciled"


@unique
class ExecutionEventType(StrEnum):
    INTENT_CREATED = "intent_created"
    RISK_CHECKED = "risk_checked"
    ORDER_SUBMITTED = "order_submitted"
    ORDER_ACKNOWLEDGED = "order_acknowledged"
    FILL_RECORDED = "fill_recorded"
    CANCEL_REQUESTED = "cancel_requested"
    ORDER_CANCELED = "order_canceled"
    ORDER_REJECTED = "order_rejected"
    ORDER_EXPIRED = "order_expired"
    RECONCILED = "reconciled"
    KILL_SWITCH_TRIGGERED = "kill_switch_triggered"


OPEN_EXECUTION_STATES: Final = frozenset(
    {
        ExecutionState.INTENT_CREATED,
        ExecutionState.RISK_CHECKED,
        ExecutionState.SUBMITTED,
        ExecutionState.ACKNOWLEDGED,
        ExecutionState.PARTIALLY_FILLED,
        ExecutionState.CANCEL_REQUESTED,
    },
)


def is_open_execution_state(state: ExecutionState) -> bool:
    return state in OPEN_EXECUTION_STATES
