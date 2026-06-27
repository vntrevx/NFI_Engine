from __future__ import annotations

import sys
from pathlib import Path
from time import perf_counter
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.domain import TradingMode
from nfi_engine.setup import RiskPreset, SetupError, SetupIntent, SetupRequest, write_setup_config
from nfi_engine.setup.credential_file import (
    SetupCredentialFileError,
    SetupCredentialValues,
    load_setup_credentials_file,
)

setup_app: Final[typer.Typer] = typer.Typer(help="Generate first-run runtime config.")
SECRET_SETUP_ARGUMENTS: Final = (
    "--api-key",
    "--api-secret",
    "--passphrase",
    "--memo",
    "--operator-id",
    "--account-address",
    "--api-wallet-signer",
)


@setup_app.command(
    "init",
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def init_setup(
    ctx: typer.Context,
    config: Annotated[Path, typer.Option("--config", dir_okay=False)],
    exchange: Annotated[str, typer.Option("--exchange")],
    trading_mode: Annotated[TradingMode, typer.Option("--trading-mode")],
    paper: Annotated[bool, typer.Option("--paper")] = False,
    testnet: Annotated[bool, typer.Option("--testnet")] = False,
    live: Annotated[bool, typer.Option("--live")] = False,
    credentials_file: Annotated[
        Path | None,
        typer.Option("--credentials-file", dir_okay=False),
    ] = None,
    risk_preset: Annotated[RiskPreset, typer.Option("--risk-preset")] = RiskPreset.BALANCED,
    non_interactive: Annotated[bool, typer.Option("--non-interactive")] = False,
    confirm_live: Annotated[bool, typer.Option("--confirm-live")] = False,
    force: Annotated[bool, typer.Option("--force")] = False,
) -> None:
    _reject_extra_args(tuple(ctx.args))
    if not non_interactive:
        _exit_with_setup_error(
            SetupError(
                code="SETUP_NON_INTERACTIVE_REQUIRED",
                message="use --non-interactive for milestone 2 setup",
            )
        )
    started_at = perf_counter()
    file_credentials = _credentials_file(credentials_file)
    request = SetupRequest(
        exchange=exchange,
        trading_mode=trading_mode,
        intent=_intent(paper=paper, testnet=testnet, live=live),
        api_key=file_credentials.api_key,
        api_secret=file_credentials.api_secret,
        passphrase=file_credentials.passphrase,
        memo=file_credentials.memo,
        operator_id=file_credentials.operator_id,
        account_address=file_credentials.account_address,
        api_wallet_signer=file_credentials.api_wallet_signer,
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


def _credentials_file(credentials_file: Path | None) -> SetupCredentialValues:
    if credentials_file is None:
        return SetupCredentialValues()
    try:
        return load_setup_credentials_file(credentials_file)
    except SetupCredentialFileError as exc:
        _exit_with_setup_error(SetupError(code=exc.code, message=exc.message))


def _reject_extra_args(extra_args: tuple[str, ...]) -> None:
    if len(extra_args) == 0:
        return
    if any(_is_secret_argument(arg) for arg in extra_args):
        _exit_with_setup_error(
            SetupError(
                code="SETUP_SECRET_ARGUMENT_REJECTED",
                message="use --credentials-file for exchange credentials",
            )
        )
    _exit_with_setup_error(
        SetupError(code="SETUP_UNKNOWN_ARGUMENT", message="unknown setup argument")
    )


def _is_secret_argument(arg: str) -> bool:
    return any(arg == flag or arg.startswith(f"{flag}=") for flag in SECRET_SETUP_ARGUMENTS)


def _exit_with_setup_error(exc: SetupError) -> NoReturn:
    sys.stderr.write(f"{exc.code}: {exc.message}\n")
    raise typer.Exit(code=1) from exc
