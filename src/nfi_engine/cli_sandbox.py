from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.compat import run_nfi_compatibility_check
from nfi_engine.sandbox import SandboxCheckResult, SandboxError, SandboxErrorCode
from nfi_engine.sandbox.service import check_strategy_sandbox
from nfi_engine.strategy import StrategyContractError

sandbox_app: Final[typer.Typer] = typer.Typer(help="Check strategy sandbox policy.")


@sandbox_app.command("check")
def check(
    strategy: Annotated[str, typer.Option("--strategy")],
    output: Annotated[Path | None, typer.Option("--output", dir_okay=False)] = None,
) -> None:
    try:
        result = check_strategy_sandbox(strategy)
        compatibility = run_nfi_compatibility_check(strategy)
    except SandboxError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except StrategyContractError as exc:
        _exit_with_error(exc.code.value, exc.message)
    if not result.passed:
        _exit_with_violation(result)
    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            compatibility.to_report().model_dump_json(indent=2) + "\n",
            encoding="utf-8",
        )
    sys.stdout.write("sandbox_passed=true\n")
    sys.stdout.write(f"approved_capabilities={','.join(result.approved_capabilities)}\n")
    sys.stdout.write(f"detected_callbacks={','.join(result.detected_callbacks)}\n")
    if output is not None:
        sys.stdout.write(f"compatibility_report={output}\n")


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
