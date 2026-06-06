from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from nfi_engine.events.models import TradingEvent
from nfi_engine.events.serialization import event_to_json_line


@dataclass(frozen=True, slots=True)
class JsonlEventSink:
    path: Path

    def write(self, event: TradingEvent) -> None:
        self.write_many((event,))

    def write_many(self, events: Iterable[TradingEvent]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as handle:
            for event in events:
                handle.write(event_to_json_line(event))
