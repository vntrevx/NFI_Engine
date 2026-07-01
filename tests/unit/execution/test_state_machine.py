from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Final

import pytest

from nfi_engine.execution import ExecutionState
from nfi_engine.execution.state_machine import (
    ExecutionStateMachineSnapshot,
    ExecutionTransitionRequest,
    ExecutionTransitionResultCode,
    apply_execution_transition,
)

NOW: Final = datetime(2026, 6, 30, 13, 0, tzinfo=UTC)
ZERO_QUANTITY: Final = Decimal(0)


def test_execution_state_machine_reaches_reconciled_with_decimal_remaining() -> None:
    snapshot = ExecutionStateMachineSnapshot.initial(requested_quantity=Decimal(1))
    for request in (
        _request(ExecutionState.RISK_CHECKED, "risk"),
        _request(ExecutionState.SUBMITTED, "submit"),
        _request(ExecutionState.ACKNOWLEDGED, "ack"),
        _request(
            ExecutionState.PARTIALLY_FILLED,
            "fill-partial",
            fill_quantity_delta=Decimal("0.40"),
        ),
        _request(
            ExecutionState.FILLED,
            "fill-rest",
            fill_quantity_delta=Decimal("0.60"),
        ),
        _request(ExecutionState.RECONCILED, "reconcile"),
    ):
        result = apply_execution_transition(snapshot, request)
        assert result.code is ExecutionTransitionResultCode.APPLIED
        snapshot = result.snapshot

    assert snapshot.state is ExecutionState.RECONCILED
    assert snapshot.filled_quantity == Decimal(1)
    assert snapshot.remaining_quantity == Decimal(0)
    assert tuple(event.to_state for event in snapshot.events) == (
        ExecutionState.RISK_CHECKED,
        ExecutionState.SUBMITTED,
        ExecutionState.ACKNOWLEDGED,
        ExecutionState.PARTIALLY_FILLED,
        ExecutionState.FILLED,
        ExecutionState.RECONCILED,
    )


@pytest.mark.parametrize(
    ("from_state", "to_state", "filled_quantity", "fill_delta"),
    [
        (ExecutionState.INTENT_CREATED, ExecutionState.RISK_CHECKED, Decimal(0), Decimal(0)),
        (ExecutionState.RISK_CHECKED, ExecutionState.SUBMITTED, Decimal(0), Decimal(0)),
        (ExecutionState.SUBMITTED, ExecutionState.ACKNOWLEDGED, Decimal(0), Decimal(0)),
        (ExecutionState.ACKNOWLEDGED, ExecutionState.PARTIALLY_FILLED, Decimal(0), Decimal("0.25")),
        (ExecutionState.ACKNOWLEDGED, ExecutionState.FILLED, Decimal(0), Decimal(1)),
        (ExecutionState.ACKNOWLEDGED, ExecutionState.CANCEL_REQUESTED, Decimal(0), Decimal(0)),
        (ExecutionState.ACKNOWLEDGED, ExecutionState.REJECTED, Decimal(0), Decimal(0)),
        (ExecutionState.ACKNOWLEDGED, ExecutionState.EXPIRED, Decimal(0), Decimal(0)),
        (
            ExecutionState.PARTIALLY_FILLED,
            ExecutionState.PARTIALLY_FILLED,
            Decimal("0.25"),
            Decimal("0.25"),
        ),
        (ExecutionState.PARTIALLY_FILLED, ExecutionState.FILLED, Decimal("0.25"), Decimal("0.75")),
        (
            ExecutionState.PARTIALLY_FILLED,
            ExecutionState.CANCEL_REQUESTED,
            Decimal("0.25"),
            Decimal(0),
        ),
        (ExecutionState.PARTIALLY_FILLED, ExecutionState.REJECTED, Decimal("0.25"), Decimal(0)),
        (ExecutionState.PARTIALLY_FILLED, ExecutionState.EXPIRED, Decimal("0.25"), Decimal(0)),
        (ExecutionState.CANCEL_REQUESTED, ExecutionState.CANCELED, Decimal(0), Decimal(0)),
        (ExecutionState.FILLED, ExecutionState.RECONCILED, Decimal(1), Decimal(0)),
        (ExecutionState.CANCELED, ExecutionState.RECONCILED, Decimal(0), Decimal(0)),
        (ExecutionState.REJECTED, ExecutionState.RECONCILED, Decimal(0), Decimal(0)),
        (ExecutionState.EXPIRED, ExecutionState.RECONCILED, Decimal(0), Decimal(0)),
    ],
)
def test_execution_state_machine_accepts_every_allowed_transition(
    from_state: ExecutionState,
    to_state: ExecutionState,
    filled_quantity: Decimal,
    fill_delta: Decimal,
) -> None:
    snapshot = ExecutionStateMachineSnapshot(
        state=from_state,
        requested_quantity=Decimal(1),
        filled_quantity=filled_quantity,
    )

    result = apply_execution_transition(
        snapshot,
        _request(to_state, f"{from_state.value}-{to_state.value}", fill_quantity_delta=fill_delta),
    )

    assert result.code is ExecutionTransitionResultCode.APPLIED
    assert result.snapshot.state is to_state
    assert len(result.snapshot.events) == 1
    assert result.appended_event is not None
    assert result.appended_event.from_state is from_state
    assert result.appended_event.to_state is to_state


def test_execution_state_machine_rejects_illegal_transition_without_extra_event() -> None:
    snapshot = ExecutionStateMachineSnapshot(
        state=ExecutionState.FILLED,
        requested_quantity=Decimal(1),
        filled_quantity=Decimal(1),
    )

    result = apply_execution_transition(
        snapshot,
        _request(ExecutionState.SUBMITTED, "filled-submit"),
    )

    assert result.code is ExecutionTransitionResultCode.TERMINAL_STATE_IMMUTABLE
    assert result.snapshot is snapshot
    assert result.appended_event is None
    assert result.machine_code == "EXECUTION_TERMINAL_STATE_IMMUTABLE"
    assert snapshot.events == ()


def test_execution_state_machine_replays_exchange_ack_idempotently() -> None:
    snapshot = ExecutionStateMachineSnapshot(
        state=ExecutionState.SUBMITTED,
        requested_quantity=Decimal(1),
    )
    request = _request(ExecutionState.ACKNOWLEDGED, "exchange-ack-1")

    applied = apply_execution_transition(snapshot, request)
    replayed = apply_execution_transition(applied.snapshot, request)

    assert applied.code is ExecutionTransitionResultCode.APPLIED
    assert replayed.code is ExecutionTransitionResultCode.REPLAYED
    assert replayed.snapshot is applied.snapshot
    assert replayed.appended_event is None
    assert len(replayed.snapshot.events) == 1


def test_execution_state_machine_keeps_reconciled_state_immutable() -> None:
    snapshot = ExecutionStateMachineSnapshot(
        state=ExecutionState.RECONCILED,
        requested_quantity=Decimal(1),
        filled_quantity=Decimal(1),
    )

    result = apply_execution_transition(
        snapshot,
        _request(ExecutionState.SUBMITTED, "reconciled-submit"),
    )

    assert result.code is ExecutionTransitionResultCode.TERMINAL_STATE_IMMUTABLE
    assert result.snapshot is snapshot
    assert result.appended_event is None


def _request(
    to_state: ExecutionState,
    event_key: str,
    *,
    fill_quantity_delta: Decimal = ZERO_QUANTITY,
) -> ExecutionTransitionRequest:
    return ExecutionTransitionRequest(
        to_state=to_state,
        event_key=event_key,
        at=NOW,
        fill_quantity_delta=fill_quantity_delta,
        message=to_state.value,
    )
