from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from nfi_engine.events import REDACTED_TEXT, EventCode, EventSeverity, TradingEvent
from nfi_engine.notifications import (
    DiscordNotifier,
    JsonlNotifier,
    NoopNotifier,
    NotificationError,
    NotificationErrorCode,
    NotificationResult,
    TelegramNotifier,
    WebhookNotifier,
    dispatch_notification,
)

FIXTURE_VALUE: Final = "telegram-fixture-value"


def test_jsonl_notifier_writes_redacted_typed_event(tmp_path: Path) -> None:
    # Given
    output = tmp_path / "notify.jsonl"
    notifier = JsonlNotifier(path=output, secrets=(FIXTURE_VALUE,))

    # When
    result = notifier.send(_event(f"smoke {FIXTURE_VALUE}"))

    # Then
    assert result.success is True
    contents = output.read_text(encoding="utf-8")
    assert "smoke" in contents
    assert REDACTED_TEXT in contents
    assert FIXTURE_VALUE not in contents


def test_webhook_notifier_builds_generic_payload_shape() -> None:
    # Given
    notifier = WebhookNotifier(url="http://127.0.0.1:18090/notify", secrets=(FIXTURE_VALUE,))

    # When
    payload = notifier.payload_for(_event(f"webhook {FIXTURE_VALUE}"))

    # Then
    assert payload.event.code == EventCode.BOT_STARTED.value
    assert payload.event.severity == EventSeverity.INFO.value
    assert payload.event.safe_summary == f"webhook {REDACTED_TEXT}"


def test_discord_notifier_builds_discord_payload_shape() -> None:
    # Given
    notifier = DiscordNotifier(
        webhook_url="http://127.0.0.1:18090/discord",
        secrets=(FIXTURE_VALUE,),
    )

    # When
    payload = notifier.payload_for(_event(f"discord {FIXTURE_VALUE}"))

    # Then
    assert payload.content == f"[INFO] discord {REDACTED_TEXT}"


def test_telegram_notifier_builds_telegram_payload_shape() -> None:
    # Given
    notifier = TelegramNotifier(
        bot_token=FIXTURE_VALUE,
        chat_id="12345",
        api_base_url="http://127.0.0.1:18090",
        secrets=(FIXTURE_VALUE,),
    )

    # When
    payload = notifier.payload_for(_event(f"telegram {FIXTURE_VALUE}"))

    # Then
    assert payload.chat_id == "12345"
    assert payload.text == f"[INFO] telegram {REDACTED_TEXT}"


def test_noop_notifier_consumes_event_without_side_effects() -> None:
    # Given
    notifier = NoopNotifier()

    # When
    result = notifier.send(_event("noop"))

    # Then
    assert result.success is True
    assert result.channel == "noop"


def test_dispatch_notification_returns_failure_instead_of_raising() -> None:
    # Given
    notifier = FailingNotifier()

    # When
    result = dispatch_notification(notifier, _event("nonblocking"))

    # Then
    assert result.success is False
    assert result.failure_code is NotificationErrorCode.NOTIFICATION_ADAPTER_FAILED


class FailingNotifier:
    @property
    def channel(self) -> str:
        return "failing"

    def send(self, event: TradingEvent) -> NotificationResult:
        raise NotificationError(
            code=NotificationErrorCode.NOTIFICATION_ADAPTER_FAILED,
            message=f"forced failure for {event.correlation_id}",
        )


def _event(summary: str) -> TradingEvent:
    return TradingEvent(
        at=datetime(2026, 1, 1, tzinfo=UTC),
        severity=EventSeverity.INFO,
        code=EventCode.BOT_STARTED,
        correlation_id="corr-notify",
        command="notify test",
        route=None,
        safe_summary=summary,
        report_hint="attach notification evidence",
    )
