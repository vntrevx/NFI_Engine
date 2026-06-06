from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from nfi_engine.events import (
    REDACTED_TEXT,
    EventCode,
    EventSeverity,
    JsonlEventSink,
    TradingEvent,
    event_from_json_line,
    event_to_json_line,
    redact_text,
)


def test_event_serialization_round_trips_with_operator_context() -> None:
    # Given
    event = TradingEvent(
        at=datetime(2026, 1, 1, tzinfo=UTC),
        severity=EventSeverity.INFO,
        code=EventCode.BOT_STARTED,
        correlation_id="corr-1",
        command="paper-run",
        route=None,
        safe_summary="paper bot started",
        report_hint="include event file",
    )

    # When
    line = event_to_json_line(event)
    parsed = event_from_json_line(line)

    # Then
    assert parsed == event
    assert "bot_started" in line
    assert "corr-1" in line


def test_jsonl_sink_writes_multiple_events(tmp_path: Path) -> None:
    # Given
    path = tmp_path / "events.jsonl"
    sink = JsonlEventSink(path)
    started = _event(EventCode.BOT_STARTED)
    stopped = _event(EventCode.BOT_STOPPED)

    # When
    sink.write_many((started, stopped))

    # Then
    content = path.read_text(encoding="utf-8")
    assert "bot_started" in content
    assert "bot_stopped" in content


def test_redaction_removes_known_secret_values() -> None:
    # Given
    fixture_value = "fixture-secret-value"

    # When
    redacted = redact_text(f"api_secret={fixture_value}", secrets=(fixture_value,))

    # Then
    assert fixture_value not in redacted
    assert REDACTED_TEXT in redacted


def _event(code: EventCode) -> TradingEvent:
    return TradingEvent(
        at=datetime(2026, 1, 1, tzinfo=UTC),
        severity=EventSeverity.INFO,
        code=code,
        correlation_id="corr-1",
        command="paper-run",
        route=None,
        safe_summary=code.value,
        report_hint="include event file",
    )
