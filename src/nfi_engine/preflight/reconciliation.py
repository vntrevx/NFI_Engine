from __future__ import annotations

from pathlib import Path

from nfi_engine.config import RuntimeSettings
from nfi_engine.preflight.models import PreflightCheck, PreflightCode, PreflightStatus
from nfi_engine.reconciliation import (
    ReconciliationError,
    load_reconciliation_fixture,
    startup_recovery_report,
)


def reconciliation_check(settings: RuntimeSettings) -> PreflightCheck:
    if not settings.reconciliation.required:
        return _check(
            PreflightCode.RECONCILIATION_READY,
            PreflightStatus.PASS,
            "startup reconciliation is not required",
        )
    fixture_path = settings.reconciliation.fixture_path
    if fixture_path is None:
        return _check(
            PreflightCode.RECONCILIATION_REQUIRED,
            PreflightStatus.BLOCK,
            "startup reconciliation fixture_path is required",
        )
    try:
        snapshot = load_reconciliation_fixture(Path(fixture_path))
        report = startup_recovery_report(snapshot=snapshot)
    except ReconciliationError as exc:
        return _check(
            PreflightCode.RECONCILIATION_REQUIRED,
            PreflightStatus.BLOCK,
            str(exc),
        )
    if report.trading_halted:
        return _check(
            PreflightCode.RECONCILIATION_REQUIRED,
            PreflightStatus.BLOCK,
            f"startup reconciliation mismatch_count={report.mismatch_count}",
        )
    return _check(
        PreflightCode.RECONCILIATION_READY,
        PreflightStatus.PASS,
        "startup reconciliation passed",
    )


def _check(
    code: PreflightCode,
    status: PreflightStatus,
    message: str,
) -> PreflightCheck:
    return PreflightCheck(code=code, status=status, message=message)
