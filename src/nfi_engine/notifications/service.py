from __future__ import annotations

from pathlib import Path
from typing import assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.events import TradingEvent
from nfi_engine.notifications.adapters import (
    DiscordNotifier,
    JsonlNotifier,
    NoopNotifier,
    TelegramNotifier,
    WebhookNotifier,
)
from nfi_engine.notifications.errors import NotificationError, NotificationErrorCode
from nfi_engine.notifications.models import NotificationChannel, NotificationResult, Notifier


def dispatch_notification(notifier: Notifier, event: TradingEvent) -> NotificationResult:
    try:
        return notifier.send(event)
    except NotificationError as exc:
        return NotificationResult(
            success=False,
            channel=notifier.channel,
            attempts=1,
            failure_code=exc.code,
            message=exc.message,
        )
    except OSError as exc:
        return NotificationResult(
            success=False,
            channel=notifier.channel,
            attempts=1,
            failure_code=NotificationErrorCode.NOTIFICATION_ADAPTER_FAILED,
            message=str(exc),
        )


def notifier_from_settings(
    *,
    settings: RuntimeSettings,
    channel: NotificationChannel,
    output: Path | None,
) -> Notifier:
    if not settings.notifications.enabled:
        return NoopNotifier()
    secrets = _notification_secrets(settings)
    timeout_seconds = float(settings.notifications.timeout_seconds)
    max_attempts = settings.notifications.max_attempts
    match channel:
        case NotificationChannel.JSONL:
            path = output if output is not None else Path(settings.notifications.jsonl_path)
            return JsonlNotifier(path=path, secrets=secrets)
        case NotificationChannel.WEBHOOK:
            return WebhookNotifier(
                url=_required(settings.notifications.webhook_url, "notifications.webhook_url"),
                secrets=secrets,
                timeout_seconds=timeout_seconds,
                max_attempts=max_attempts,
            )
        case NotificationChannel.DISCORD:
            return DiscordNotifier(
                webhook_url=_required(
                    settings.notifications.discord_webhook_url,
                    "notifications.discord_webhook_url",
                ),
                secrets=secrets,
                timeout_seconds=timeout_seconds,
                max_attempts=max_attempts,
            )
        case NotificationChannel.TELEGRAM:
            return TelegramNotifier(
                bot_token=_required(
                    settings.notifications.telegram_bot_token,
                    "notifications.telegram_bot_token",
                ),
                chat_id=_required(
                    settings.notifications.telegram_chat_id,
                    "notifications.telegram_chat_id",
                ),
                api_base_url=settings.notifications.telegram_api_base_url,
                secrets=secrets,
                timeout_seconds=timeout_seconds,
                max_attempts=max_attempts,
            )
        case NotificationChannel.NOOP:
            return NoopNotifier()
        case unreachable:
            assert_never(unreachable)


def _required(value: str | None, path: str) -> str:
    if value is not None and value != "":
        return value
    raise NotificationError(
        code=NotificationErrorCode.NOTIFICATION_CONFIG_INVALID,
        message=f"missing required notifier setting: {path}",
    )


def _notification_secrets(settings: RuntimeSettings) -> tuple[str, ...]:
    candidates = (
        settings.exchange.api_key,
        settings.exchange.api_secret,
        settings.notifications.webhook_url,
        settings.notifications.discord_webhook_url,
        settings.notifications.telegram_bot_token,
    )
    return tuple(value for value in candidates if value is not None and value != "")
