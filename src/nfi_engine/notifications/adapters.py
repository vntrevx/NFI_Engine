from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import httpx

from nfi_engine.events import JsonlEventSink, TradingEvent
from nfi_engine.notifications.errors import NotificationErrorCode
from nfi_engine.notifications.models import NotificationChannel, NotificationResult
from nfi_engine.notifications.payloads import (
    DiscordPayload,
    HttpNotificationPayload,
    TelegramPayload,
    WebhookPayload,
    event_payload,
    event_text,
    redacted_event,
)


@dataclass(frozen=True, slots=True)
class NoopNotifier:
    @property
    def channel(self) -> str:
        return NotificationChannel.NOOP.value

    def send(self, event: TradingEvent) -> NotificationResult:
        return NotificationResult(
            success=True,
            channel=self.channel,
            attempts=1,
            message=f"consumed={event.correlation_id}",
        )


@dataclass(frozen=True, slots=True)
class JsonlNotifier:
    path: Path
    secrets: tuple[str, ...] = ()

    @property
    def channel(self) -> str:
        return NotificationChannel.JSONL.value

    def send(self, event: TradingEvent) -> NotificationResult:
        JsonlEventSink(self.path).write(redacted_event(event, secrets=self.secrets))
        return NotificationResult(success=True, channel=self.channel, attempts=1)


@dataclass(frozen=True, slots=True)
class WebhookNotifier:
    url: str
    secrets: tuple[str, ...] = ()
    timeout_seconds: float = 3
    max_attempts: int = 2

    @property
    def channel(self) -> str:
        return NotificationChannel.WEBHOOK.value

    def payload_for(self, event: TradingEvent) -> WebhookPayload:
        return WebhookPayload(event=event_payload(event, secrets=self.secrets))

    def send(self, event: TradingEvent) -> NotificationResult:
        return _post_json(
            channel=self.channel,
            url=self.url,
            payload=self.payload_for(event),
            timeout_seconds=self.timeout_seconds,
            max_attempts=self.max_attempts,
        )


@dataclass(frozen=True, slots=True)
class DiscordNotifier:
    webhook_url: str
    secrets: tuple[str, ...] = ()
    timeout_seconds: float = 3
    max_attempts: int = 2

    @property
    def channel(self) -> str:
        return NotificationChannel.DISCORD.value

    def payload_for(self, event: TradingEvent) -> DiscordPayload:
        return DiscordPayload(content=event_text(event, secrets=self.secrets))

    def send(self, event: TradingEvent) -> NotificationResult:
        return _post_json(
            channel=self.channel,
            url=self.webhook_url,
            payload=self.payload_for(event),
            timeout_seconds=self.timeout_seconds,
            max_attempts=self.max_attempts,
        )


@dataclass(frozen=True, slots=True)
class TelegramNotifier:
    bot_token: str
    chat_id: str
    api_base_url: str = "https://api.telegram.org"
    secrets: tuple[str, ...] = ()
    timeout_seconds: float = 3
    max_attempts: int = 2

    @property
    def channel(self) -> str:
        return NotificationChannel.TELEGRAM.value

    @property
    def url(self) -> str:
        return f"{self.api_base_url}/bot{self.bot_token}/sendMessage"

    def payload_for(self, event: TradingEvent) -> TelegramPayload:
        return TelegramPayload(
            chat_id=self.chat_id,
            text=event_text(event, secrets=self.secrets),
        )

    def send(self, event: TradingEvent) -> NotificationResult:
        return _post_json(
            channel=self.channel,
            url=self.url,
            payload=self.payload_for(event),
            timeout_seconds=self.timeout_seconds,
            max_attempts=self.max_attempts,
        )


def _post_json(
    *,
    channel: str,
    url: str,
    payload: HttpNotificationPayload,
    timeout_seconds: float,
    max_attempts: int,
) -> NotificationResult:
    attempts = max(1, max_attempts)
    failure_code = NotificationErrorCode.NOTIFICATION_HTTP_ERROR
    failure_message = "request failed"
    with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
        for attempt in range(1, attempts + 1):
            try:
                response = client.post(url, json=payload.model_dump(mode="json"))
                response.raise_for_status()
                return NotificationResult(success=True, channel=channel, attempts=attempt)
            except httpx.TimeoutException:
                failure_code = NotificationErrorCode.NOTIFICATION_TIMEOUT
                failure_message = "request timed out"
            except httpx.HTTPStatusError as exc:
                failure_code = NotificationErrorCode.NOTIFICATION_HTTP_ERROR
                failure_message = f"http_status={exc.response.status_code}"
            except httpx.TransportError:
                failure_code = NotificationErrorCode.NOTIFICATION_HTTP_ERROR
                failure_message = "transport error"
    return NotificationResult(
        success=False,
        channel=channel,
        attempts=attempts,
        failure_code=failure_code,
        message=failure_message,
    )
