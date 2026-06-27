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


class TestnetPilotReport(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    exchange: str
    trading_mode: str
    testnet: bool
    pilot_ready: bool
    live_money_orders_enabled: bool
    sample_client_order_id: str
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
