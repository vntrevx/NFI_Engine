from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict
from pydantic_core import ValidationError

from nfi_engine.events import EventCode, TradingEvent, event_from_json_line
from nfi_engine.observability.errors import EventLogError, EventLogErrorCode


class EventExplanation(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    code: str
    correlation_id: str
    safe_summary: str
    report_hint: str


def load_events(path: Path) -> tuple[TradingEvent, ...]:
    events: list[TradingEvent] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if line.strip() == "":
            continue
        try:
            events.append(event_from_json_line(line))
        except ValidationError as exc:
            raise EventLogError(
                code=EventLogErrorCode.EVENT_LOG_PARSE_ERROR,
                message=f"event JSONL parse failed at line {line_number}",
            ) from exc
    return tuple(events)


def filter_events(events: tuple[TradingEvent, ...], *, query: str) -> tuple[TradingEvent, ...]:
    normalized_query = query.lower()
    return tuple(
        event
        for event in events
        if normalized_query in event.code.value.lower()
        or normalized_query in event.safe_summary.lower()
    )


def explain_event_code(code: str, *, events: tuple[TradingEvent, ...]) -> EventExplanation:
    matched = _find_event(code=code, events=events)
    if matched is not None:
        return EventExplanation(
            code=matched.code.value,
            correlation_id=matched.correlation_id,
            safe_summary=matched.safe_summary,
            report_hint=matched.report_hint,
        )
    return EventExplanation(
        code=code,
        correlation_id="not-found",
        safe_summary=_default_summary(code),
        report_hint=_default_report_hint(code),
    )


def _find_event(*, code: str, events: tuple[TradingEvent, ...]) -> TradingEvent | None:
    for event in events:
        if event.code.value == code:
            return event
    return None


def _default_summary(code: str) -> str:
    if code == EventCode.CONFIG_VALIDATION_ERROR.value:
        return "config validation failed"
    return "event code was not found in the provided log"


def _default_report_hint(code: str) -> str:
    if code == EventCode.CONFIG_VALIDATION_ERROR.value:
        return "attach redacted config, command output, and event JSONL"
    return "attach command output and recent event JSONL"
