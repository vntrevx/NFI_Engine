from __future__ import annotations

from typing import Final

from nfi_engine.dashboard.models import (
    DashboardExecutionSignal,
    DashboardReadModels,
)
from nfi_engine.dashboard.truth_models import DashboardAccountTruth
from nfi_engine.safety.execution_signals import (
    EXECUTION_SAFETY_SIGNALS,
    ExecutionSafetySignalDefinition,
)

EXECUTION_SIGNAL_STATUS: Final = "required"


def build_dashboard_execution_signals(
    *,
    read_models: DashboardReadModels,
    account_truth: DashboardAccountTruth,
) -> tuple[DashboardExecutionSignal, ...]:
    return tuple(
        _execution_signal(
            signal,
            read_models=read_models,
            account_truth=account_truth,
        )
        for signal in EXECUTION_SAFETY_SIGNALS
    )


def _execution_signal(
    signal: ExecutionSafetySignalDefinition,
    *,
    read_models: DashboardReadModels,
    account_truth: DashboardAccountTruth,
) -> DashboardExecutionSignal:
    status = EXECUTION_SIGNAL_STATUS
    detail = signal.detail
    if signal.code == "order_lifecycle" and (
        read_models.execution_intents != () or read_models.recent_execution_events != ()
    ):
        status = "pass"
        detail = "Execution lifecycle rows are available from the bounded ledger read model."
    if signal.code == "reconciliation":
        status, detail = _reconciliation_signal(account_truth)
    if signal.code == "partial_fill_exposure":
        status, detail = _partial_fill_signal(account_truth)
    return DashboardExecutionSignal(
        code=signal.code,
        title=signal.title,
        status=status,
        detail=detail,
    )


def _reconciliation_signal(account_truth: DashboardAccountTruth) -> tuple[str, str]:
    reconciliation = account_truth.reconciliation
    if reconciliation.status == "clear":
        return "pass", "Latest reconciliation event is clear for new entries."
    if reconciliation.status == "blocked":
        issue_codes = ", ".join(reconciliation.issue_codes) or "blocking mismatch"
        return (
            "blocked",
            f"{reconciliation.mismatch_count} reconciliation mismatch(es): {issue_codes}.",
        )
    if reconciliation.status == "missing":
        return "required", "No reconciliation event has been recorded yet."
    return "warn", "Latest reconciliation event could not be classified."


def _partial_fill_signal(account_truth: DashboardAccountTruth) -> tuple[str, str]:
    partial_fills = account_truth.exposure.partial_fills
    if partial_fills <= 0:
        return "pass", "No partial-fill exposure is open in the bounded read model."
    return "warn", f"{partial_fills} partial-fill order(s) need exposure review."
