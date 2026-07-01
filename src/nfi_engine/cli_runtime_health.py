from __future__ import annotations

import json
import sys
from enum import StrEnum, unique
from pathlib import Path
from typing import Annotated, NoReturn, assert_never

import anyio
import typer

from nfi_engine.api.runtime_health_models import RuntimeHealthResponse
from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.dashboard import DashboardReadModels
from nfi_engine.paper import BotState
from nfi_engine.preflight.service import run_preflight
from nfi_engine.profiles.catalog import default_profile_name
from nfi_engine.runtime_health import RuntimeHealthRequest, RuntimeHealthSnapshot
from nfi_engine.runtime_health.service import build_runtime_health_snapshot
from nfi_engine.wallet import fetch_wallet_balance


@unique
class RuntimeHealthFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


runtime_health_app = typer.Typer(help="Inspect lightweight runtime health checks.")


@runtime_health_app.command("check")
def check_runtime_health(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    output_format: Annotated[
        RuntimeHealthFormat,
        typer.Option("--format"),
    ] = RuntimeHealthFormat.TEXT,
    exchange_api_errors: Annotated[int, typer.Option("--exchange-api-errors", min=0)] = 0,
) -> None:
    try:
        snapshot = anyio.run(
            _build_snapshot,
            config,
            exchange_api_errors,
        )
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    sys.stdout.write(_format_snapshot(snapshot=snapshot, output_format=output_format))
    if snapshot.state.value == "blocked":
        raise typer.Exit(code=1)


async def _build_snapshot(config: Path, exchange_api_errors: int) -> RuntimeHealthSnapshot:
    settings = load_runtime_settings(config)
    readiness = run_preflight(
        settings=settings,
        profile_name=default_profile_name(settings),
        config_path=config,
    )
    wallet = await fetch_wallet_balance(settings=settings)
    return build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=settings,
            bot_state=BotState.STOPPED,
            readiness=readiness,
            read_models=DashboardReadModels.empty(),
            wallet_balance=wallet,
            exchange_api_errors=exchange_api_errors,
        ),
    )


def _format_snapshot(
    *,
    snapshot: RuntimeHealthSnapshot,
    output_format: RuntimeHealthFormat,
) -> str:
    match output_format:
        case RuntimeHealthFormat.JSON:
            payload = RuntimeHealthResponse.from_snapshot(snapshot).model_dump(mode="json")
            return json.dumps(payload, indent=2, sort_keys=True) + "\n"
        case RuntimeHealthFormat.TEXT:
            return _format_text(snapshot)
        case unreachable:
            assert_never(unreachable)


def _format_text(snapshot: RuntimeHealthSnapshot) -> str:
    lines = [
        f"runtime_health_state={snapshot.state.value}",
        f"next_action={snapshot.next_action}",
        f"database_state={snapshot.database.state.value}",
        f"database_readable={str(snapshot.database.readable).lower()}",
        f"database_writable={str(snapshot.database.writable).lower()}",
    ]
    lines.extend(
        f"check={check.code.value}\tstate={check.state.value}\tnext_action={check.next_action}"
        for check in snapshot.checks
    )
    return "\n".join(lines) + "\n"


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
