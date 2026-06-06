from __future__ import annotations

import sys
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.compat import run_nfi_compatibility_check
from nfi_engine.strategy import StrategyContractError

compat_app: Final[typer.Typer] = typer.Typer(help="Inspect strategy compatibility surfaces.")


@compat_app.command("nfi-check")
def nfi_check(strategy: Annotated[str, typer.Option("--strategy")]) -> None:
    try:
        result = run_nfi_compatibility_check(strategy)
    except StrategyContractError as exc:
        _exit_with_error(exc.code.value, exc.message)
    sys.stdout.write(f"compatible={str(result.compatible).lower()}\n")
    sys.stdout.write(f"full_x7_parity={str(result.full_x7_parity).lower()}\n")
    sys.stdout.write(f"upstream_sha={result.upstream_sha}\n")
    sys.stdout.write(f"detected_callbacks={','.join(result.detected_callbacks)}\n")
    sys.stdout.write(f"unsupported_surfaces={','.join(result.unsupported_surfaces)}\n")


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
