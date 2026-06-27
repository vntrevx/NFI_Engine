from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict


@unique
class TestnetPilotControlStatus(StrEnum):
    CLEAR = "clear"
    BLOCK = "block"


@unique
class TestnetPilotState(StrEnum):
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


class TestnetPilotControl(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    stage: str
    status: TestnetPilotControlStatus
    code: str
    message: str
    next_action: str


class TestnetPilotStateTransition(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    from_state: TestnetPilotState
    to_state: TestnetPilotState
    trigger: str
    idempotent: bool


class TestnetPilotExecutionPlan(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    client_order_id: str
    dry_run_preview_required: bool
    kill_switch_required: bool
    reconciliation_required: bool
    idempotency_key_source: str
    transitions: tuple[TestnetPilotStateTransition, ...]


class TestnetPilotReport(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    exchange: str
    trading_mode: str
    testnet: bool
    pilot_ready: bool
    live_money_orders_enabled: bool
    sample_client_order_id: str
    execution_plan: TestnetPilotExecutionPlan
    states: tuple[TestnetPilotState, ...]
    controls: tuple[TestnetPilotControl, ...]
    blockers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ControlDraft:
    stage: str
    code: str
    message: str
    next_action: str


PILOT_STATES: Final = (
    TestnetPilotState.INTENT_CREATED,
    TestnetPilotState.RISK_CHECKED,
    TestnetPilotState.SUBMITTED,
    TestnetPilotState.ACKNOWLEDGED,
    TestnetPilotState.PARTIALLY_FILLED,
    TestnetPilotState.FILLED,
    TestnetPilotState.CANCEL_REQUESTED,
    TestnetPilotState.CANCELED,
    TestnetPilotState.REJECTED,
    TestnetPilotState.EXPIRED,
    TestnetPilotState.RECONCILED,
)

PILOT_TRANSITIONS: Final = (
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.INTENT_CREATED,
        to_state=TestnetPilotState.RISK_CHECKED,
        trigger="risk_accept",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.RISK_CHECKED,
        to_state=TestnetPilotState.SUBMITTED,
        trigger="submit_with_client_order_id",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.SUBMITTED,
        to_state=TestnetPilotState.ACKNOWLEDGED,
        trigger="exchange_ack",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.ACKNOWLEDGED,
        to_state=TestnetPilotState.PARTIALLY_FILLED,
        trigger="partial_fill",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.PARTIALLY_FILLED,
        to_state=TestnetPilotState.FILLED,
        trigger="fill_complete",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.ACKNOWLEDGED,
        to_state=TestnetPilotState.CANCEL_REQUESTED,
        trigger="kill_switch_or_cancel",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.CANCEL_REQUESTED,
        to_state=TestnetPilotState.CANCELED,
        trigger="exchange_cancel_ack",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.ACKNOWLEDGED,
        to_state=TestnetPilotState.REJECTED,
        trigger="exchange_reject",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.ACKNOWLEDGED,
        to_state=TestnetPilotState.EXPIRED,
        trigger="exchange_expire",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.FILLED,
        to_state=TestnetPilotState.RECONCILED,
        trigger="startup_or_post_order_reconcile",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.CANCELED,
        to_state=TestnetPilotState.RECONCILED,
        trigger="startup_or_post_order_reconcile",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.REJECTED,
        to_state=TestnetPilotState.RECONCILED,
        trigger="startup_or_post_order_reconcile",
        idempotent=True,
    ),
    TestnetPilotStateTransition(
        from_state=TestnetPilotState.EXPIRED,
        to_state=TestnetPilotState.RECONCILED,
        trigger="startup_or_post_order_reconcile",
        idempotent=True,
    ),
)


def pass_control(draft: ControlDraft) -> TestnetPilotControl:
    return TestnetPilotControl(
        stage=draft.stage,
        status=TestnetPilotControlStatus.CLEAR,
        code=draft.code,
        message=draft.message,
        next_action=draft.next_action,
    )


def block_control(draft: ControlDraft) -> TestnetPilotControl:
    return TestnetPilotControl(
        stage=draft.stage,
        status=TestnetPilotControlStatus.BLOCK,
        code=draft.code,
        message=draft.message,
        next_action=draft.next_action,
    )
