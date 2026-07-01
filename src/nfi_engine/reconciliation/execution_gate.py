from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Protocol

from nfi_engine.execution import ExecutionEventType, ExecutionState
from nfi_engine.persistence.records import ExecutionEventRecord
from nfi_engine.reconciliation.models import ReconciliationReport, ReconciliationSnapshot
from nfi_engine.reconciliation.service import reconcile_snapshot


class ReconciliationEventSink(Protocol):
    async def append(self, record: ExecutionEventRecord) -> None: ...


@dataclass(frozen=True, slots=True)
class ReconciliationGateRequest:
    snapshot: ReconciliationSnapshot
    intent_id: str
    occurred_at: datetime
    dry_run: bool = True


@dataclass(frozen=True, slots=True)
class ReconciliationGateResult:
    report: ReconciliationReport
    event: ExecutionEventRecord

    @property
    def can_submit_new_entries(self) -> bool:
        return not self.report.trading_halted


async def record_reconciliation_gate(
    *,
    request: ReconciliationGateRequest,
    event_sink: ReconciliationEventSink,
) -> ReconciliationGateResult:
    report = reconcile_snapshot(snapshot=request.snapshot, dry_run=request.dry_run)
    event = _reconciliation_event(request=request, report=report)
    await event_sink.append(event)
    return ReconciliationGateResult(report=report, event=event)


def _reconciliation_event(
    *,
    request: ReconciliationGateRequest,
    report: ReconciliationReport,
) -> ExecutionEventRecord:
    raw_status_code = _raw_status_code(report)
    return ExecutionEventRecord(
        event_id=None,
        intent_id=request.intent_id,
        event_type=ExecutionEventType.RECONCILED,
        state=ExecutionState.RECONCILED,
        message=_event_message(report),
        raw_status_code=raw_status_code,
        metadata_json=_metadata_json(report),
        occurred_at=request.occurred_at,
    )


def _raw_status_code(report: ReconciliationReport) -> str:
    if report.trading_halted:
        return "RECONCILIATION_BLOCKED"
    return "RECONCILIATION_CLEAR"


def _event_message(report: ReconciliationReport) -> str:
    if report.trading_halted:
        return "reconciliation blocked new entries"
    return "reconciliation clear"


def _metadata_json(report: ReconciliationReport) -> str:
    payload = {
        "apply": report.apply,
        "issue_codes": [issue.code.value for issue in report.issues],
        "mismatch_count": report.mismatch_count,
        "trading_halted": report.trading_halted,
    }
    return json.dumps(payload, separators=(",", ":"), sort_keys=True)
