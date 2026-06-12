from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.domain import TradingMode
from nfi_engine.setup import RiskPreset, SetupError, SetupIntent, SetupRequest, write_setup_config

setup_app: Final[typer.Typer] = typer.Typer(help="Generate first-run runtime config.")


@setup_app.command("init")
def init_setup(
    config: Annotated[Path, typer.Option("--config", dir_okay=False)],
    exchange: Annotated[str, typer.Option("--exchange")],
    trading_mode: Annotated[TradingMode, typer.Option("--trading-mode")],
    paper: Annotated[bool, typer.Option("--paper")] = False,
    testnet: Annotated[bool, typer.Option("--testnet")] = False,
    live: Annotated[bool, typer.Option("--live")] = False,
    api_key: Annotated[str, typer.Option("--api-key", envvar="NFI_ENGINE_SETUP_API_KEY")] = "",
    api_secret: Annotated[
        str,
        typer.Option("--api-secret", envvar="NFI_ENGINE_SETUP_API_SECRET"),
    ] = "",
    risk_preset: Annotated[RiskPreset, typer.Option("--risk-preset")] = RiskPreset.BALANCED,
    non_interactive: Annotated[bool, typer.Option("--non-interactive")] = False,
    confirm_live: Annotated[bool, typer.Option("--confirm-live")] = False,
    force: Annotated[bool, typer.Option("--force")] = False,
) -> None:
    if not non_interactive:
        _exit_with_setup_error(
            SetupError(
                code="SETUP_NON_INTERACTIVE_REQUIRED",
                message="use --non-interactive for milestone 2 setup",
            )
        )
    started_at = perf_counter()
    request = SetupRequest(
        exchange=exchange,
        trading_mode=trading_mode,
        intent=_intent(paper=paper, testnet=testnet, live=live),
        api_key=api_key,
        api_secret=api_secret,
        risk_preset=risk_preset,
        live_trading_confirmed=confirm_live,
    )
    try:
        plan = write_setup_config(request=request, config_path=config, overwrite=force)
    except SetupError as exc:
        _exit_with_setup_error(exc)
    duration_ms = int((perf_counter() - started_at) * 1000)
    sys.stdout.write(f"setup_config={plan.config_path}\n")
    sys.stdout.write(f"trading_mode={request.trading_mode.value}\n")
    sys.stdout.write(f"intent={request.intent.value}\n")
    sys.stdout.write("secrets=redacted\n")
    sys.stdout.write(f"duration_ms={duration_ms}\n")


def _intent(*, paper: bool, testnet: bool, live: bool) -> SetupIntent:
    selected = sum((paper, testnet, live))
    if selected > 1:
        _exit_with_setup_error(
            SetupError(code="SETUP_INTENT_CONFLICT", message="choose only one setup intent")
        )
    if testnet:
        return SetupIntent.TESTNET
    if live:
        return SetupIntent.LIVE
    return SetupIntent.PAPER


def _exit_with_setup_error(exc: SetupError) -> NoReturn:
    sys.stderr.write(f"{exc.code}: {exc.message}\n")
    raise typer.Exit(code=1) from exc
