from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique
from typing import Final, assert_never

from nfi_engine.execution.models import ExecutionEventType, ExecutionState

ZERO_QUANTITY: Final = Decimal(0)

_ALLOWED_TRANSITIONS: Final = frozenset(
    {
        (ExecutionState.INTENT_CREATED, ExecutionState.RISK_CHECKED),
        (ExecutionState.RISK_CHECKED, ExecutionState.SUBMITTED),
        (ExecutionState.SUBMITTED, ExecutionState.ACKNOWLEDGED),
        (ExecutionState.ACKNOWLEDGED, ExecutionState.PARTIALLY_FILLED),
        (ExecutionState.ACKNOWLEDGED, ExecutionState.FILLED),
        (ExecutionState.ACKNOWLEDGED, ExecutionState.CANCEL_REQUESTED),
        (ExecutionState.ACKNOWLEDGED, ExecutionState.REJECTED),
        (ExecutionState.ACKNOWLEDGED, ExecutionState.EXPIRED),
        (ExecutionState.PARTIALLY_FILLED, ExecutionState.PARTIALLY_FILLED),
        (ExecutionState.PARTIALLY_FILLED, ExecutionState.FILLED),
        (ExecutionState.PARTIALLY_FILLED, ExecutionState.CANCEL_REQUESTED),
        (ExecutionState.PARTIALLY_FILLED, ExecutionState.REJECTED),
        (ExecutionState.PARTIALLY_FILLED, ExecutionState.EXPIRED),
        (ExecutionState.CANCEL_REQUESTED, ExecutionState.CANCELED),
        (ExecutionState.FILLED, ExecutionState.RECONCILED),
        (ExecutionState.CANCELED, ExecutionState.RECONCILED),
        (ExecutionState.REJECTED, ExecutionState.RECONCILED),
        (ExecutionState.EXPIRED, ExecutionState.RECONCILED),
    },
)
_EVENT_TYPES_BY_STATE: Final = {
    ExecutionState.INTENT_CREATED: ExecutionEventType.INTENT_CREATED,
    ExecutionState.RISK_CHECKED: ExecutionEventType.RISK_CHECKED,
    ExecutionState.SUBMITTED: ExecutionEventType.ORDER_SUBMITTED,
    ExecutionState.ACKNOWLEDGED: ExecutionEventType.ORDER_ACKNOWLEDGED,
    ExecutionState.PARTIALLY_FILLED: ExecutionEventType.FILL_RECORDED,
    ExecutionState.FILLED: ExecutionEventType.FILL_RECORDED,
    ExecutionState.CANCEL_REQUESTED: ExecutionEventType.CANCEL_REQUESTED,
    ExecutionState.CANCELED: ExecutionEventType.ORDER_CANCELED,
    ExecutionState.REJECTED: ExecutionEventType.ORDER_REJECTED,
    ExecutionState.EXPIRED: ExecutionEventType.ORDER_EXPIRED,
    ExecutionState.RECONCILED: ExecutionEventType.RECONCILED,
}


@unique
class ExecutionTransitionResultCode(StrEnum):
    APPLIED = "EXECUTION_TRANSITION_APPLIED"
    DUPLICATE_EVENT_KEY = "EXECUTION_DUPLICATE_EVENT_KEY"
    ILLEGAL_TRANSITION = "EXECUTION_TRANSITION_ILLEGAL"
    INVALID_FILL_QUANTITY = "EXECUTION_INVALID_FILL_QUANTITY"
    REPLAYED = "EXECUTION_TRANSITION_REPLAYED"
    TERMINAL_STATE_IMMUTABLE = "EXECUTION_TERMINAL_STATE_IMMUTABLE"


@dataclass(frozen=True, slots=True)
class ExecutionStateMachineEvent:
    event_key: str
    event_type: ExecutionEventType
    from_state: ExecutionState
    to_state: ExecutionState
    at: datetime
    message: str
    fill_quantity_delta: Decimal = ZERO_QUANTITY


@dataclass(frozen=True, slots=True)
class ExecutionStateMachineSnapshot:
    state: ExecutionState
    requested_quantity: Decimal
    filled_quantity: Decimal = ZERO_QUANTITY
    events: tuple[ExecutionStateMachineEvent, ...] = ()

    @classmethod
    def initial(cls, *, requested_quantity: Decimal) -> ExecutionStateMachineSnapshot:
        return cls(
            state=ExecutionState.INTENT_CREATED,
            requested_quantity=requested_quantity,
        )

    @property
    def remaining_quantity(self) -> Decimal:
        remaining = self.requested_quantity - self.filled_quantity
        if remaining < ZERO_QUANTITY:
            return ZERO_QUANTITY
        return remaining


@dataclass(frozen=True, slots=True)
class ExecutionTransitionRequest:
    to_state: ExecutionState
    event_key: str
    at: datetime
    fill_quantity_delta: Decimal = ZERO_QUANTITY
    message: str = ""


@dataclass(frozen=True, slots=True)
class ExecutionTransitionResult:
    code: ExecutionTransitionResultCode
    snapshot: ExecutionStateMachineSnapshot
    appended_event: ExecutionStateMachineEvent | None = None

    @property
    def machine_code(self) -> str:
        return self.code.value


def apply_execution_transition(
    snapshot: ExecutionStateMachineSnapshot,
    request: ExecutionTransitionRequest,
) -> ExecutionTransitionResult:
    replay = _find_existing_event(snapshot.events, request.event_key)
    if replay is not None:
        return _replay_result(snapshot, replay, request)

    if _is_immutable_terminal_transition(snapshot.state, request.to_state):
        return ExecutionTransitionResult(
            code=ExecutionTransitionResultCode.TERMINAL_STATE_IMMUTABLE,
            snapshot=snapshot,
        )

    if (snapshot.state, request.to_state) not in _ALLOWED_TRANSITIONS:
        return ExecutionTransitionResult(
            code=ExecutionTransitionResultCode.ILLEGAL_TRANSITION,
            snapshot=snapshot,
        )

    next_filled_quantity = _next_filled_quantity(snapshot, request)
    if next_filled_quantity is None:
        return ExecutionTransitionResult(
            code=ExecutionTransitionResultCode.INVALID_FILL_QUANTITY,
            snapshot=snapshot,
        )

    event = ExecutionStateMachineEvent(
        event_key=request.event_key,
        event_type=_event_type_for(request.to_state),
        from_state=snapshot.state,
        to_state=request.to_state,
        at=request.at,
        message=request.message,
        fill_quantity_delta=request.fill_quantity_delta,
    )
    next_snapshot = ExecutionStateMachineSnapshot(
        state=request.to_state,
        requested_quantity=snapshot.requested_quantity,
        filled_quantity=next_filled_quantity,
        events=(*snapshot.events, event),
    )
    return ExecutionTransitionResult(
        code=ExecutionTransitionResultCode.APPLIED,
        snapshot=next_snapshot,
        appended_event=event,
    )


def _find_existing_event(
    events: tuple[ExecutionStateMachineEvent, ...],
    event_key: str,
) -> ExecutionStateMachineEvent | None:
    for event in events:
        if event.event_key == event_key:
            return event
    return None


def _replay_result(
    snapshot: ExecutionStateMachineSnapshot,
    replay: ExecutionStateMachineEvent,
    request: ExecutionTransitionRequest,
) -> ExecutionTransitionResult:
    if replay.to_state is request.to_state:
        return ExecutionTransitionResult(
            code=ExecutionTransitionResultCode.REPLAYED,
            snapshot=snapshot,
        )
    return ExecutionTransitionResult(
        code=ExecutionTransitionResultCode.DUPLICATE_EVENT_KEY,
        snapshot=snapshot,
    )


def _is_immutable_terminal_transition(
    from_state: ExecutionState,
    to_state: ExecutionState,
) -> bool:
    match from_state:
        case ExecutionState.RECONCILED:
            return True
        case (
            ExecutionState.FILLED
            | ExecutionState.CANCELED
            | ExecutionState.REJECTED
            | ExecutionState.EXPIRED
        ):
            return to_state is not ExecutionState.RECONCILED
        case (
            ExecutionState.INTENT_CREATED
            | ExecutionState.RISK_CHECKED
            | ExecutionState.SUBMITTED
            | ExecutionState.ACKNOWLEDGED
            | ExecutionState.PARTIALLY_FILLED
            | ExecutionState.CANCEL_REQUESTED
        ):
            return False
        case unreachable:
            assert_never(unreachable)


def _next_filled_quantity(
    snapshot: ExecutionStateMachineSnapshot,
    request: ExecutionTransitionRequest,
) -> Decimal | None:
    match request.to_state:
        case ExecutionState.PARTIALLY_FILLED:
            return _next_partial_fill_quantity(snapshot, request)
        case ExecutionState.FILLED:
            return _next_terminal_fill_quantity(snapshot, request)
        case (
            ExecutionState.INTENT_CREATED
            | ExecutionState.RISK_CHECKED
            | ExecutionState.SUBMITTED
            | ExecutionState.ACKNOWLEDGED
            | ExecutionState.CANCEL_REQUESTED
            | ExecutionState.CANCELED
            | ExecutionState.REJECTED
            | ExecutionState.EXPIRED
            | ExecutionState.RECONCILED
        ):
            return _unchanged_fill_quantity(snapshot, request)
        case unreachable:
            assert_never(unreachable)


def _next_partial_fill_quantity(
    snapshot: ExecutionStateMachineSnapshot,
    request: ExecutionTransitionRequest,
) -> Decimal | None:
    next_quantity = snapshot.filled_quantity + request.fill_quantity_delta
    if ZERO_QUANTITY < next_quantity < snapshot.requested_quantity:
        return next_quantity
    return None


def _next_terminal_fill_quantity(
    snapshot: ExecutionStateMachineSnapshot,
    request: ExecutionTransitionRequest,
) -> Decimal | None:
    fill_delta = request.fill_quantity_delta
    if fill_delta == ZERO_QUANTITY:
        return snapshot.requested_quantity
    next_quantity = snapshot.filled_quantity + fill_delta
    if next_quantity == snapshot.requested_quantity:
        return next_quantity
    return None


def _unchanged_fill_quantity(
    snapshot: ExecutionStateMachineSnapshot,
    request: ExecutionTransitionRequest,
) -> Decimal | None:
    if request.fill_quantity_delta == ZERO_QUANTITY:
        return snapshot.filled_quantity
    return None


def _event_type_for(to_state: ExecutionState) -> ExecutionEventType:
    return _EVENT_TYPES_BY_STATE[to_state]
