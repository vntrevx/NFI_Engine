from __future__ import annotations

import sys
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.sandbox import SandboxCheckResult, SandboxError, SandboxErrorCode
from nfi_engine.sandbox.service import check_strategy_sandbox
from nfi_engine.strategy import StrategyContractError

sandbox_app: Final[typer.Typer] = typer.Typer(help="Check strategy sandbox policy.")


@sandbox_app.command("check")
def check(strategy: Annotated[str, typer.Option("--strategy")]) -> None:
    try:
        result = check_strategy_sandbox(strategy)
    except SandboxError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except StrategyContractError as exc:
        _exit_with_error(exc.code.value, exc.message)
    if not result.passed:
        _exit_with_violation(result)
    sys.stdout.write("sandbox_passed=true\n")
    sys.stdout.write(f"approved_capabilities={','.join(result.approved_capabilities)}\n")
    sys.stdout.write(f"detected_callbacks={','.join(result.detected_callbacks)}\n")


def _exit_with_violation(result: SandboxCheckResult) -> NoReturn:
    first = result.violations[0]
    sys.stderr.write(
        (
            f"{SandboxErrorCode.SANDBOX_VIOLATION.value}: "
            f"{first.kind.value} line={first.line} {first.message}\n"
        ),
    )
    raise typer.Exit(code=1)


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
