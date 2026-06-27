from __future__ import annotations

from typing import Protocol, Self, TypedDict

from nfi_engine.config.models import RuntimeSettings
from nfi_engine.events import redact_text


class LogEntryUpdate(TypedDict):
    message: str
    command: str | None
    route: str | None
    safe_summary: str
    report_hint: str


class RedactableLogEntry(Protocol):
    message: str
    command: str | None
    route: str | None
    safe_summary: str
    report_hint: str

    def model_copy(self, *, update: LogEntryUpdate) -> Self: ...


def redacted_support_logs[LogEntryT: RedactableLogEntry](
    *,
    settings: RuntimeSettings,
    logs: tuple[LogEntryT, ...],
) -> tuple[LogEntryT, ...]:
    secrets = _support_secret_values(settings)
    if len(secrets) == 0:
        return logs
    return tuple(_redacted_log_entry(log, secrets=secrets) for log in logs)


def _redacted_log_entry[LogEntryT: RedactableLogEntry](
    log: LogEntryT,
    *,
    secrets: tuple[str, ...],
) -> LogEntryT:
    return log.model_copy(
        update={
            "message": redact_text(log.message, secrets=secrets),
            "command": _redacted_optional(log.command, secrets=secrets),
            "route": _redacted_optional(log.route, secrets=secrets),
            "safe_summary": redact_text(log.safe_summary, secrets=secrets),
            "report_hint": redact_text(log.report_hint, secrets=secrets),
        },
    )


def _redacted_optional(text: str | None, *, secrets: tuple[str, ...]) -> str | None:
    if text is None:
        return None
    return redact_text(text, secrets=secrets)


def _support_secret_values(settings: RuntimeSettings) -> tuple[str, ...]:
    values = (
        settings.exchange.api_key,
        settings.exchange.api_secret,
        settings.exchange.passphrase,
        settings.exchange.memo,
        settings.exchange.operator_id,
        settings.exchange.account_address,
        settings.exchange.api_wallet_signer,
        settings.api.auth_token,
        settings.api.operator_password,
        settings.notifications.webhook_url,
        settings.notifications.discord_webhook_url,
        settings.notifications.telegram_bot_token,
    )
    return tuple(value for value in values if value is not None and value != "")
