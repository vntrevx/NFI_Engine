from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.api.models import config_current_response
from nfi_engine.config import ConfigLoadError, load_runtime_settings, render_frontend_metadata
from nfi_engine.maintenance import (
    MaintenanceError,
    build_config_history,
    build_config_migration_plan,
    preview_config_rollback,
)

config_app: Final[typer.Typer] = typer.Typer(help="Validate and inspect runtime config.")


@config_app.command("validate")
def validate_config(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
) -> None:
    try:
        settings = load_runtime_settings(config)
    except ConfigLoadError as exc:
        _exit_with_config_error(exc)
    sys.stdout.write("valid\n")
    sys.stdout.write(f"trading_mode={settings.exchange.trading_mode.value}\n")
    sys.stdout.write(f"live_trading={str(settings.engine.live_trading).lower()}\n")


@config_app.command("show")
def show_config(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        settings = load_runtime_settings(config)
    except ConfigLoadError as exc:
        _exit_with_config_error(exc)
    payload = config_current_response(settings)
    if json_output:
        sys.stdout.write(payload.model_dump_json(indent=2))
        sys.stdout.write("\n")
        return
    sys.stdout.write(f"environment={payload.engine.environment}\n")
    sys.stdout.write(f"exchange={payload.exchange.name}\n")
    sys.stdout.write(f"trading_mode={payload.exchange.trading_mode}\n")
    sys.stdout.write(f"api_auth_token={payload.api.auth_token}\n")


@config_app.command("schema")
def schema_config(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    frontend: Annotated[bool, typer.Option("--frontend")] = False,
) -> None:
    try:
        load_runtime_settings(config)
    except ConfigLoadError as exc:
        _exit_with_config_error(exc)
    if frontend:
        sys.stdout.write("\n".join(render_frontend_metadata()))
        sys.stdout.write("\n")
        return
    sys.stdout.write("schema=runtime_settings\n")


@config_app.command("migrate")
def migrate_config(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    backup_reference: Annotated[str | None, typer.Option("--backup-reference")] = None,
    allow_no_backup_for_dev: Annotated[bool, typer.Option("--allow-no-backup-for-dev")] = False,
) -> None:
    try:
        plan = build_config_migration_plan(
            config=config,
            dry_run=dry_run,
            backup_reference=backup_reference,
            allow_no_backup_for_dev=allow_no_backup_for_dev,
        )
    except MaintenanceError as exc:
        _exit_with_maintenance_error(exc)
    sys.stdout.write("migration_plan=config\n")
    sys.stdout.write(f"config={plan.config}\n")
    sys.stdout.write(f"current_schema_version={plan.current_schema_version}\n")
    sys.stdout.write(f"target_schema_version={plan.target_schema_version}\n")
    sys.stdout.write(f"apply={str(plan.apply).lower()}\n")
    for step in plan.steps:
        sys.stdout.write(f"step={step}\n")


@config_app.command("history")
def history_config(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
) -> None:
    try:
        entry = build_config_history(config=config)
    except MaintenanceError as exc:
        _exit_with_maintenance_error(exc)
    sys.stdout.write(f"version={entry.version}\n")
    sys.stdout.write(f"schema_version={entry.schema_version}\n")
    sys.stdout.write(f"config_hash={entry.config_hash}\n")
    sys.stdout.write(f"strategy_name={entry.strategy_name}\n")
    sys.stdout.write(f"strategy_module={entry.strategy_module}\n")


@config_app.command("rollback")
def rollback_config(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    to_version: Annotated[str, typer.Option("--to-version")],
    backup_reference: Annotated[str | None, typer.Option("--backup-reference")] = None,
    dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = False,
    allow_no_backup_for_dev: Annotated[bool, typer.Option("--allow-no-backup-for-dev")] = False,
) -> None:
    try:
        plan = preview_config_rollback(
            config=config,
            to_version=to_version,
            apply=not dry_run,
            backup_reference=backup_reference,
            allow_no_backup_for_dev=allow_no_backup_for_dev,
        )
    except MaintenanceError as exc:
        _exit_with_maintenance_error(exc)
    sys.stdout.write("rollback_plan=config\n")
    sys.stdout.write(f"config={plan.config}\n")
    sys.stdout.write(f"to_version={plan.to_version}\n")
    sys.stdout.write(f"apply={str(plan.apply).lower()}\n")
    for step in plan.steps:
        sys.stdout.write(f"step={step}\n")


def _exit_with_config_error(exc: ConfigLoadError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc


def _exit_with_maintenance_error(exc: MaintenanceError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc
