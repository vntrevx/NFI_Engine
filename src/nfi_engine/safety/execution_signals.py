from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class ExecutionSafetySignalDefinition:
    code: str
    title: str
    detail: str


EXECUTION_SAFETY_SIGNALS: Final[tuple[ExecutionSafetySignalDefinition, ...]] = (
    ExecutionSafetySignalDefinition(
        code="order_lifecycle",
        title="Order lifecycle",
        detail=(
            "Intent, placement, open, partial, filled, canceled, rejected, and failed "
            "states must stay traceable."
        ),
    ),
    ExecutionSafetySignalDefinition(
        code="reconciliation",
        title="Reconciliation",
        detail=(
            "Local orders, positions, and balances must be checked against exchange "
            "or account truth."
        ),
    ),
    ExecutionSafetySignalDefinition(
        code="idempotency",
        title="Idempotency",
        detail=(
            "Stable client order ids must make retries safe before any live order lane is promoted."
        ),
    ),
    ExecutionSafetySignalDefinition(
        code="kill_switch",
        title="Kill switch",
        detail="Manual halt and emergency stop state must block new order placement.",
    ),
    ExecutionSafetySignalDefinition(
        code="circuit_breakers",
        title="Circuit breakers",
        detail=(
            "Loss, stale data, API error, rejection, slippage, funding, and exposure "
            "gates must stay visible."
        ),
    ),
    ExecutionSafetySignalDefinition(
        code="partial_fill_exposure",
        title="Partial-fill exposure",
        detail="Remaining quantity and exposure must be visible when fills are partial.",
    ),
)

EXECUTION_SAFETY_SIGNAL_CODES: Final[tuple[str, ...]] = tuple(
    signal.code for signal in EXECUTION_SAFETY_SIGNALS
)
