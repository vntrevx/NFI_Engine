from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar, Final

import pytest
from pydantic import BaseModel, ConfigDict

from nfi_engine.execution import ExecutionEventType, ExecutionState
from nfi_engine.persistence.records import ExecutionEventRecord
from nfi_engine.reconciliation import (
    ReconciliationCode,
    ReconciliationGateRequest,
    load_reconciliation_fixture,
    record_reconciliation_gate,
)

pytestmark = pytest.mark.anyio

NOW: Final = datetime(2026, 1, 1, 9, 30, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_reconciliation_gate_appends_clear_event_when_snapshots_match() -> None:
    # Given
    event_sink = MemoryExecutionEventSink()
    snapshot = load_reconciliation_fixture(Path("tests/fixtures/exchange/reconcile_match.json"))
    request = ReconciliationGateRequest(
        snapshot=snapshot,
        intent_id="intent-clear",
        occurred_at=NOW,
    )

    # When
    result = await record_reconciliation_gate(request=request, event_sink=event_sink)

    # Then
    assert result.report.trading_halted is False
    assert result.can_submit_new_entries is True
    assert len(event_sink.records) == 1
    event = event_sink.records[0]
    assert event.intent_id == "intent-clear"
    assert event.event_type is ExecutionEventType.RECONCILED
    assert event.state is ExecutionState.RECONCILED
    assert event.raw_status_code == "RECONCILIATION_CLEAR"
    assert event.message == "reconciliation clear"
    metadata = GateEventMetadata.model_validate_json(event.metadata_json)
    assert metadata == GateEventMetadata(
        apply=False,
        issue_codes=(),
        mismatch_count=0,
        trading_halted=False,
    )


async def test_reconciliation_gate_blocks_and_appends_safe_issue_summary() -> None:
    # Given
    event_sink = MemoryExecutionEventSink()
    snapshot = load_reconciliation_fixture(
        Path("tests/fixtures/exchange/reconcile_mismatch.json"),
    )
    request = ReconciliationGateRequest(
        snapshot=snapshot,
        intent_id="intent-blocked",
        occurred_at=NOW,
    )

    # When
    result = await record_reconciliation_gate(request=request, event_sink=event_sink)

    # Then
    expected_codes = {
        ReconciliationCode.ORPHAN_LOCAL_ORDER.value,
        ReconciliationCode.ORPHAN_EXCHANGE_ORDER.value,
        ReconciliationCode.MISSING_EXCHANGE_FILL.value,
        ReconciliationCode.PENDING_CANCEL.value,
        ReconciliationCode.POSITION_MISMATCH.value,
        ReconciliationCode.LEVERAGE_MISMATCH.value,
        ReconciliationCode.MARGIN_MODE_MISMATCH.value,
        ReconciliationCode.BALANCE_MISMATCH.value,
        ReconciliationCode.STALE_LOCK.value,
        ReconciliationCode.DUPLICATE_LOCAL_TRADE.value,
    }
    assert result.report.trading_halted is True
    assert result.can_submit_new_entries is False
    assert {issue.code.value for issue in result.report.issues} == expected_codes
    assert all(issue.suggested_action.startswith("dry-run:") for issue in result.report.issues)
    assert len(event_sink.records) == 1
    event = event_sink.records[0]
    assert event.event_type is ExecutionEventType.RECONCILED
    assert event.state is ExecutionState.RECONCILED
    assert event.raw_status_code == "RECONCILIATION_BLOCKED"
    assert event.message == "reconciliation blocked new entries"
    metadata = GateEventMetadata.model_validate_json(event.metadata_json)
    assert metadata.apply is False
    assert metadata.trading_halted is True
    assert metadata.mismatch_count == len(result.report.issues)
    assert set(metadata.issue_codes) == expected_codes
    assert "local-only" not in event.metadata_json
    assert "exchange-only" not in event.metadata_json
    assert "duplicate-trade" not in event.metadata_json


@dataclass(slots=True)
class MemoryExecutionEventSink:
    records: list[ExecutionEventRecord] = field(default_factory=list)

    async def append(self, record: ExecutionEventRecord) -> None:
        self.records.append(record)


class GateEventMetadata(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    apply: bool
    issue_codes: tuple[str, ...]
    mismatch_count: int
    trading_halted: bool
