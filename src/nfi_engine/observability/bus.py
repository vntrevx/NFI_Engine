from __future__ import annotations

from dataclasses import dataclass, field

from nfi_engine.events import TradingEvent


@dataclass(slots=True)
class EventBus:
    """Mutable because websocket/API consumers need a shared in-memory event stream."""

    _events: list[TradingEvent] = field(default_factory=list)

    def publish(self, event: TradingEvent) -> None:
        self._events.append(event)

    def recent(self, *, limit: int) -> tuple[TradingEvent, ...]:
        return tuple(self._events[-limit:])
