from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.events import EventCode, EventSeverity, TradingEvent
from nfi_engine.notifications import (
    NotificationChannel,
    NotificationError,
    dispatch_notification,
    notifier_from_settings,
)
from nfi_engine.observability import new_correlation_id

notify_app: Final[typer.Typer] = typer.Typer(help="Send typed test notifications.")


@notify_app.command("test")
def send_test_notification(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    channel: Annotated[NotificationChannel, typer.Option("--channel")],
    message: Annotated[str, typer.Option("--message")],
    output: Annotated[Path | None, typer.Option("--output", dir_okay=False)] = None,
) -> None:
    try:
        settings = load_runtime_settings(config)
        notifier = notifier_from_settings(settings=settings, channel=channel, output=output)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except NotificationError as exc:
        _exit_with_error(exc.code.value, exc.message)
    result = dispatch_notification(notifier, _test_event(message))
    sys.stdout.write(f"channel={result.channel}\n")
    sys.stdout.write(f"notification_failed={str(not result.success).lower()}\n")
    sys.stdout.write(f"attempts={result.attempts}\n")
    failure_code = "none" if result.failure_code is None else result.failure_code.value
    sys.stdout.write(f"failure_code={failure_code}\n")
    if result.message != "":
        sys.stdout.write(f"message={result.message}\n")


def _test_event(message: str) -> TradingEvent:
    return TradingEvent(
        at=datetime.now(UTC),
        severity=EventSeverity.INFO,
        code=EventCode.NOTIFICATION_TEST,
        correlation_id=new_correlation_id(),
        command="notify test",
        route=None,
        safe_summary=message,
        report_hint="attach notify test CLI output and local notification artifact",
    )


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
