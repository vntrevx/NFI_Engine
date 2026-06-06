from __future__ import annotations

from datetime import datetime
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from nfi_engine.events import TradingEvent, redact_text


class StrictNotificationModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


class NotificationEventPayload(StrictNotificationModel):
    at: datetime
    severity: str
    code: str
    correlation_id: str
    command: str | None
    route: str | None
    safe_summary: str
    report_hint: str


class WebhookPayload(StrictNotificationModel):
    event: NotificationEventPayload


class DiscordPayload(StrictNotificationModel):
    content: str


class TelegramPayload(StrictNotificationModel):
    chat_id: str
    text: str


type HttpNotificationPayload = WebhookPayload | DiscordPayload | TelegramPayload


def redacted_event(event: TradingEvent, *, secrets: tuple[str, ...]) -> TradingEvent:
    return event.model_copy(
        update={
            "safe_summary": redact_text(event.safe_summary, secrets=secrets),
            "report_hint": redact_text(event.report_hint, secrets=secrets),
        },
    )


def event_payload(event: TradingEvent, *, secrets: tuple[str, ...]) -> NotificationEventPayload:
    redacted = redacted_event(event, secrets=secrets)
    return NotificationEventPayload(
        at=redacted.at,
        severity=redacted.severity.value,
        code=redacted.code.value,
        correlation_id=redacted.correlation_id,
        command=redacted.command,
        route=redacted.route,
        safe_summary=redacted.safe_summary,
        report_hint=redacted.report_hint,
    )


def event_text(event: TradingEvent, *, secrets: tuple[str, ...]) -> str:
    redacted = redacted_event(event, secrets=secrets)
    return f"[{redacted.severity.value}] {redacted.safe_summary}"
