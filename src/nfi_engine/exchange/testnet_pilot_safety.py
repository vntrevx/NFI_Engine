from __future__ import annotations

from decimal import Decimal
from typing import Final

from nfi_engine.config import RuntimeSettings
from nfi_engine.preflight.reconciliation import reconciliation_check

from .testnet_pilot_models import (
    ControlDraft,
    TestnetPilotControl,
    block_control,
    pass_control,
)

ZERO: Final = Decimal(0)


def reconciliation_gate_check(settings: RuntimeSettings) -> TestnetPilotControl:
    if not settings.reconciliation.required or settings.reconciliation.fixture_path is None:
        return block_control(
            ControlDraft(
                stage="reconciliation",
                code="TESTNET_PILOT_RECONCILIATION_REQUIRED",
                message="Startup reconciliation must be required and fixture-backed.",
                next_action="Set reconciliation.required=true with a checked fixture path.",
            ),
        )
    check = reconciliation_check(settings)
    if check.status.value == "PASS":
        return pass_control(
            ControlDraft(
                stage="reconciliation",
                code="TESTNET_PILOT_RECONCILIATION_READY",
                message="Startup reconciliation fixture passes.",
                next_action="Run reconciliation again before each pilot session.",
            ),
        )
    return block_control(
        ControlDraft(
            stage="reconciliation",
            code="TESTNET_PILOT_RECONCILIATION_BLOCKED",
            message=check.message,
            next_action="Fix reconciliation mismatches before allowing pilot entries.",
        ),
    )


def circuit_breaker_check(settings: RuntimeSettings) -> TestnetPilotControl:
    gaps = _circuit_breaker_gaps(settings)
    if not gaps:
        return pass_control(
            ControlDraft(
                stage="circuit_breaker",
                code="TESTNET_PILOT_CIRCUIT_BREAKERS_READY",
                message="Circuit breakers and manual halt file are configured.",
                next_action="Touch the manual halt file to stop new entries during incidents.",
            ),
        )
    return block_control(
        ControlDraft(
            stage="circuit_breaker",
            code="TESTNET_PILOT_CIRCUIT_BREAKERS_INCOMPLETE",
            message=f"Circuit breaker gaps: {', '.join(gaps)}.",
            next_action="Configure bounded loss, freshness, API error, and manual halt controls.",
        ),
    )


def _circuit_breaker_gaps(settings: RuntimeSettings) -> tuple[str, ...]:
    circuit = settings.circuit_breakers
    gaps: list[str] = []
    if not circuit.enabled:
        gaps.append("enabled")
    if circuit.max_daily_loss_usdt <= ZERO:
        gaps.append("max_daily_loss_usdt")
    if circuit.max_drawdown_pct <= ZERO:
        gaps.append("max_drawdown_pct")
    if circuit.max_stale_seconds <= 0:
        gaps.append("max_stale_seconds")
    if circuit.max_api_errors <= 0:
        gaps.append("max_api_errors")
    if circuit.max_rejected_orders <= 0:
        gaps.append("max_rejected_orders")
    if not _present(circuit.manual_halt_file):
        gaps.append("manual_halt_file")
    return tuple(gaps)


def _present(value: str | None) -> bool:
    return value is not None and value.strip() != ""
