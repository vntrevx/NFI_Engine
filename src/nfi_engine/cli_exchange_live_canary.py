from __future__ import annotations

import sys
from decimal import Decimal, InvalidOperation
from functools import partial
from pathlib import Path
from typing import Annotated, NoReturn

import anyio
import typer

from nfi_engine.config import ConfigLoadError, RuntimeSettings, load_runtime_settings
from nfi_engine.exchange.live_canary import build_live_canary_preview
from nfi_engine.exchange.live_canary_models import LiveCanaryPreview
from nfi_engine.exchange.live_canary_order import (
    LIVE_CANARY_EXECUTION_PHRASE,
    run_live_canary_order,
)
from nfi_engine.exchange.live_canary_order_models import LiveCanaryOrderReport
from nfi_engine.persistence import create_persistence_database


def run_live_canary_cli(  # noqa: PLR0913
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    preview: Annotated[bool, typer.Option("--preview/--no-preview")] = False,
    execute: Annotated[bool, typer.Option("--execute/--no-execute")] = False,
    preview_hash: Annotated[str | None, typer.Option("--preview-hash")] = None,
    confirmation_hash: Annotated[str | None, typer.Option("--confirm-hash")] = None,
    confirmation_phrase: Annotated[str | None, typer.Option("--confirm-order-phrase")] = None,
    reference_price_usdt: Annotated[str | None, typer.Option("--reference-price-usdt")] = None,
    json_output: Annotated[bool, typer.Option("--json/--text")] = False,
) -> None:
    if not preview and not execute:
        _exit_with_error(
            "LIVE_CANARY_PREVIEW_REQUIRED",
            "Pass --preview for read-only preview or --execute with explicit confirmations.",
        )
    try:
        settings = load_runtime_settings(config)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    if execute:
        report = _run_execution(
            settings=settings,
            preview_hash=preview_hash,
            confirmation_hash=confirmation_hash,
            confirmation_phrase=confirmation_phrase,
            reference_price_usdt=reference_price_usdt,
        )
        if json_output:
            sys.stdout.write(report.model_dump_json(indent=2) + "\n")
            if not report.ready:
                raise typer.Exit(code=1)
            return
        write_live_canary_order_report(report)
        if not report.ready:
            raise typer.Exit(code=1)
        return
    report = build_live_canary_preview(settings=settings, config_path=config)
    if json_output:
        sys.stdout.write(report.model_dump_json(indent=2) + "\n")
        return
    write_live_canary_preview(report)


def write_live_canary_preview(report: LiveCanaryPreview) -> None:
    sys.stdout.write(f"ready={str(report.ready).lower()}\n")
    sys.stdout.write(f"preview_hash={report.preview_hash}\n")
    sys.stdout.write(f"exchange={report.exchange}\n")
    sys.stdout.write(f"production={str(report.production).lower()}\n")
    sys.stdout.write(f"testnet={str(report.testnet).lower()}\n")
    sys.stdout.write("order_would_be_submitted=false\n")
    sys.stdout.write("adapter_constructed=false\n")
    sys.stdout.write(f"blockers={','.join(report.blockers) if report.blockers else 'none'}\n")
    sys.stdout.write(f"rollback_command={report.rollback_command}\n")
    for check in report.checks:
        sys.stdout.write(
            f"check={check.code.value}\tstate={check.state.value}\tmessage={check.message}\n",
        )


def write_live_canary_order_report(report: LiveCanaryOrderReport) -> None:
    sys.stdout.write(f"ready={str(report.ready).lower()}\n")
    sys.stdout.write(f"executed={str(report.executed).lower()}\n")
    sys.stdout.write(f"live_money_orders_enabled={str(report.live_money_orders_enabled).lower()}\n")
    sys.stdout.write(f"duplicate_rejected={str(report.duplicate_rejected).lower()}\n")
    sys.stdout.write(f"preview_hash={report.preview_hash}\n")
    sys.stdout.write(f"client_order_id={report.client_order_id or 'none'}\n")
    sys.stdout.write(f"entry_order_id={report.entry_order_id or 'none'}\n")
    sys.stdout.write(f"exit_order_id={report.exit_order_id or 'none'}\n")
    sys.stdout.write(f"blockers={','.join(report.blockers) if report.blockers else 'none'}\n")
    for event in report.events:
        sys.stdout.write(f"event={event.event_type.value}\tmessage={event.message}\n")


def _run_execution(
    *,
    settings: RuntimeSettings,
    preview_hash: str | None,
    confirmation_hash: str | None,
    confirmation_phrase: str | None,
    reference_price_usdt: str | None,
) -> LiveCanaryOrderReport:
    if preview_hash is None or confirmation_hash is None:
        _exit_with_error(
            "LIVE_CANARY_PREVIEW_HASH_REQUIRED", "Pass --preview-hash and --confirm-hash."
        )
    if confirmation_phrase != LIVE_CANARY_EXECUTION_PHRASE:
        _exit_with_error(
            "LIVE_CANARY_EXECUTION_CONFIRMATION",
            f"Pass --confirm-order-phrase {LIVE_CANARY_EXECUTION_PHRASE}.",
        )
    if reference_price_usdt is None:
        _exit_with_error(
            "LIVE_CANARY_REFERENCE_PRICE_REQUIRED",
            "Pass --reference-price-usdt with the operator-reviewed reference price.",
        )
    try:
        parsed_reference_price = Decimal(reference_price_usdt)
    except InvalidOperation:
        _exit_with_error(
            "LIVE_CANARY_REFERENCE_PRICE_INVALID",
            "Pass a finite decimal --reference-price-usdt.",
        )
    database = create_persistence_database(settings.database.url)
    try:
        return anyio.run(
            partial(
                run_live_canary_order,
                settings=settings,
                database=database,
                preview_hash=preview_hash,
                confirmation_hash=confirmation_hash,
                confirmation_phrase=confirmation_phrase,
                reference_price_usdt=parsed_reference_price,
            ),
        )
    finally:
        anyio.run(database.dispose)


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
