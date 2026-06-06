from __future__ import annotations

from nfi_engine.events.models import TradingEvent


def event_to_json_line(event: TradingEvent) -> str:
    return event.model_dump_json() + "\n"


def event_from_json_line(line: str) -> TradingEvent:
    return TradingEvent.model_validate_json(line)
