from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.observability import EventLogError, explain_event_code, load_events

logs_app: Final[typer.Typer] = typer.Typer(help="Inspect operator event logs.")


@logs_app.command("explain")
def explain_log_code(
    code: Annotated[str, typer.Argument()],
    events: Annotated[Path, typer.Option("--events", exists=True, dir_okay=False)],
) -> None:
    try:
        loaded_events = load_events(events)
    except EventLogError as exc:
        _exit_with_error(exc.code.value, exc.message)
    explanation = explain_event_code(code, events=loaded_events)
    sys.stdout.write(f"code={explanation.code}\n")
    sys.stdout.write(f"correlation_id={explanation.correlation_id}\n")
    sys.stdout.write(f"safe_summary={explanation.safe_summary}\n")
    sys.stdout.write(f"report_hint={explanation.report_hint}\n")


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
