from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from nfi_engine.events import EventCode, EventSeverity, TradingEvent
from nfi_engine.observability import (
    EventBus,
    EventLogError,
    explain_event_code,
    filter_events,
    load_events,
    new_correlation_id,
)


def test_event_bus_fanout_keeps_recent_events() -> None:
    # Given
    bus = EventBus()
    event = _event(EventCode.BOT_STARTED, correlation_id="corr-bus")

    # When
    bus.publish(event)

    # Then
    assert bus.recent(limit=5) == (event,)


def test_correlation_ids_are_reportable_identifiers() -> None:
    # Given/When
    correlation_id = new_correlation_id()

    # Then
    assert len(correlation_id) >= 20
    assert "-" in correlation_id


def test_error_catalog_lookup_returns_report_hint() -> None:
    # Given
    event = _event(EventCode.CONFIG_VALIDATION_ERROR, correlation_id="corr-config")

    # When
    explanation = explain_event_code(EventCode.CONFIG_VALIDATION_ERROR.value, events=(event,))

    # Then
    assert explanation.code == "CONFIG_VALIDATION_ERROR"
    assert explanation.correlation_id == "corr-config"
    assert "config" in explanation.safe_summary
    assert "report" in explanation.report_hint


def test_log_filtering_matches_code_and_summary() -> None:
    # Given
    config_event = _event(EventCode.CONFIG_VALIDATION_ERROR, correlation_id="corr-config")
    bot_event = _event(
        EventCode.BOT_STARTED,
        correlation_id="corr-bot",
        safe_summary="bot started",
    )

    # When
    filtered = filter_events((config_event, bot_event), query="config")

    # Then
    assert filtered == (config_event,)


def test_load_events_raises_typed_error_for_malformed_jsonl(tmp_path: Path) -> None:
    # Given
    path = tmp_path / "bad-events.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")

    # When/Then
    with pytest.raises(EventLogError, match="EVENT_LOG_PARSE_ERROR"):
        load_events(path)


def _event(
    code: EventCode,
    *,
    correlation_id: str,
    safe_summary: str = "config validation failed",
) -> TradingEvent:
    return TradingEvent(
        at=datetime(2026, 1, 1, tzinfo=UTC),
        severity=EventSeverity.ERROR,
        code=code,
        correlation_id=correlation_id,
        command="config validate",
        route=None,
        safe_summary=safe_summary,
        report_hint="attach report bundle",
    )
