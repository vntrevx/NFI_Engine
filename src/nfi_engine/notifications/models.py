from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import Protocol

from nfi_engine.events import TradingEvent
from nfi_engine.notifications.errors import NotificationErrorCode


@unique
class NotificationChannel(StrEnum):
    DISCORD = "discord"
    JSONL = "jsonl"
    NOOP = "noop"
    TELEGRAM = "telegram"
    WEBHOOK = "webhook"


@dataclass(frozen=True, slots=True)
class NotificationResult:
    success: bool
    channel: str
    attempts: int
    failure_code: NotificationErrorCode | None = None
    message: str = ""


class Notifier(Protocol):
    @property
    def channel(self) -> str: ...

    def send(self, event: TradingEvent) -> NotificationResult: ...
