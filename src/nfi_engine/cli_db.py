from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Final, NoReturn

import anyio
import typer
from sqlalchemy.exc import SQLAlchemyError

from nfi_engine.config import ConfigLoadError, RuntimeSettings, load_runtime_settings
from nfi_engine.domain import PositionSide, TradeState
from nfi_engine.maintenance import MaintenanceError, build_database_migration_plan
from nfi_engine.persistence import create_persistence_database
from nfi_engine.persistence.records import TradeRecord
from nfi_engine.persistence.repositories import TradeRepository

db_app: Final[typer.Typer] = typer.Typer(help="Initialize and inspect persistence storage.")


@db_app.command("init")
def init_database(
    database_url: Annotated[str | None, typer.Option("--database-url")] = None,
    config: Annotated[Path | None, typer.Option("--config", exists=True, dir_okay=False)] = None,
) -> None:
    try:
        resolved_url = _resolve_database_url(database_url=database_url, config=config)
        anyio.run(_init_database, resolved_url)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except SQLAlchemyError as exc:
        _exit_with_error("PERSISTENCE_ERROR", str(exc))
    sys.stdout.write(f"initialized database_url={resolved_url}\n")


@db_app.command("smoke")
def smoke_database(
    database_url: Annotated[str | None, typer.Option("--database-url")] = None,
    config: Annotated[Path | None, typer.Option("--config", exists=True, dir_okay=False)] = None,
) -> None:
    try:
        resolved_url = _resolve_database_url(database_url=database_url, config=config)
        trade_id = anyio.run(_smoke_database, resolved_url)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except SQLAlchemyError as exc:
        _exit_with_error("PERSISTENCE_ERROR", str(exc))
    sys.stdout.write(f"created trade id={trade_id}\n")
    sys.stdout.write(f"loaded trade id={trade_id}\n")


@db_app.command("migrate")
def migrate_database(
    database: Annotated[Path, typer.Option("--database", exists=True, dir_okay=False)],
    dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    backup_reference: Annotated[str | None, typer.Option("--backup-reference")] = None,
    allow_no_backup_for_dev: Annotated[bool, typer.Option("--allow-no-backup-for-dev")] = False,
) -> None:
    try:
        plan = build_database_migration_plan(
            database=database,
            dry_run=dry_run,
            backup_reference=backup_reference,
            allow_no_backup_for_dev=allow_no_backup_for_dev,
        )
    except MaintenanceError as exc:
        _exit_with_error(exc.code.value, exc.message)
    sys.stdout.write("migration_plan=database\n")
    sys.stdout.write(f"database={plan.database}\n")
    sys.stdout.write(f"current_version={plan.current_version}\n")
    sys.stdout.write(f"target_version={plan.target_version}\n")
    sys.stdout.write(f"apply={str(plan.apply).lower()}\n")
    for step in plan.steps:
        sys.stdout.write(f"step={step}\n")


def _resolve_database_url(*, database_url: str | None, config: Path | None) -> str:
    if database_url is not None:
        return database_url
    if config is not None:
        settings = load_runtime_settings(config)
        return _database_url_from_settings(settings)
    return _exit_with_error("DATABASE_URL_REQUIRED", "pass --database-url or --config")


def _database_url_from_settings(settings: RuntimeSettings) -> str:
    return settings.database.url


async def _init_database(database_url: str) -> None:
    database = create_persistence_database(database_url)
    try:
        await database.initialize()
    finally:
        await database.dispose()


async def _smoke_database(database_url: str) -> str:
    database = create_persistence_database(database_url)
    try:
        await database.initialize()
        record = _smoke_trade()
        async with database.session() as session:
            repository = TradeRepository(session)
            existing = await repository.get(record.trade_id)
            if existing is None:
                await repository.create(record)
                await session.commit()
        async with database.session() as session:
            loaded = await TradeRepository(session).get(record.trade_id)
        if loaded is None:
            _exit_with_error("PERSISTENCE_SMOKE_FAILED", "trade was not loaded after create")
        return loaded.trade_id
    finally:
        await database.dispose()


def _smoke_trade() -> TradeRecord:
    return TradeRecord(
        trade_id="smoke-trade",
        pair="BTC/USDT",
        side=PositionSide.LONG,
        state=TradeState.OPEN,
        opened_at=datetime(2026, 1, 1, tzinfo=UTC),
        closed_at=None,
        entry_price=Decimal(100),
        exit_price=None,
        quantity=Decimal("0.1"),
        leverage=Decimal(1),
        profit=Decimal(0),
    )


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
