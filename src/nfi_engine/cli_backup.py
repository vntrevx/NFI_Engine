from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.maintenance import (
    BackupRestorePlan,
    BackupResult,
    BackupVerification,
    MaintenanceError,
    create_backup,
    preview_backup_restore,
    verify_backup,
)

backup_app: Final[typer.Typer] = typer.Typer(help="Create, verify, and restore backups.")


@backup_app.command("create")
def create_backup_command(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option("--output")],
) -> None:
    try:
        result = create_backup(config=config, output=output)
    except MaintenanceError as exc:
        _exit_with_error(exc)
    _write_backup_result(result)


@backup_app.command("verify")
def verify_backup_command(
    archive: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
) -> None:
    try:
        verification = verify_backup(archive)
    except MaintenanceError as exc:
        _exit_with_error(exc)
    _write_backup_verification(verification)


@backup_app.command("restore")
def restore_backup_command(
    archive: Annotated[Path, typer.Argument(exists=True, dir_okay=False)],
    dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
) -> None:
    try:
        plan = preview_backup_restore(archive=archive, dry_run=dry_run)
    except MaintenanceError as exc:
        _exit_with_error(exc)
    _write_restore_plan(plan)


def _write_backup_result(result: BackupResult) -> None:
    sys.stdout.write("backup_created=true\n")
    sys.stdout.write(f"output={result.output}\n")
    sys.stdout.write(f"manifest_valid={str(result.manifest_valid).lower()}\n")
    sys.stdout.write(f"redacted={str(result.redacted).lower()}\n")
    sys.stdout.write(f"entries={','.join(result.entries)}\n")


def _write_backup_verification(verification: BackupVerification) -> None:
    sys.stdout.write(f"archive={verification.archive}\n")
    sys.stdout.write(f"manifest_valid={str(verification.manifest_valid).lower()}\n")
    sys.stdout.write(f"redacted={str(verification.redacted).lower()}\n")
    sys.stdout.write(f"entries={','.join(verification.entries)}\n")


def _write_restore_plan(plan: BackupRestorePlan) -> None:
    sys.stdout.write("restore_plan=backup\n")
    sys.stdout.write(f"archive={plan.archive}\n")
    sys.stdout.write(f"apply={str(plan.apply).lower()}\n")
    sys.stdout.write(f"manifest_valid={str(plan.manifest_valid).lower()}\n")
    for step in plan.steps:
        sys.stdout.write(f"step={step}\n")


def _exit_with_error(exc: MaintenanceError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc
