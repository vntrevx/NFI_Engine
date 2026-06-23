from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final

import typer

from nfi_engine.preflight import PreflightReport
from nfi_engine.preflight.service import run_preflight_for_config

preflight_app: Final[typer.Typer] = typer.Typer(help="Run operator readiness checks.")


@preflight_app.command("check")
def check_preflight(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    profile_name: Annotated[str, typer.Option("--profile")],
) -> None:
    report = run_preflight_for_config(config_path=config, profile_name=profile_name)
    _write_report(report)
    if report.blocked:
        raise typer.Exit(code=1)


def _write_report(report: PreflightReport) -> None:
    summary = "PREFLIGHT_BLOCKED" if report.blocked else "PREFLIGHT_PASSED"
    sys.stdout.write(f"{summary}\n")
    sys.stdout.write(f"profile={report.profile}\n")
    for check in report.checks:
        sys.stdout.write(f"{check.status.value}\t{check.code.value}\t{check.message}\n")
