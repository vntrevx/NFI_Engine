from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.benchmark import (
    BenchmarkError,
    build_m2_report,
    regression_messages,
    write_report,
)

DEFAULT_CONFIG: Final = Path("examples/futures-paper.yaml")
DEFAULT_OUTPUT: Final = Path(".omo/evidence/m2-benchmark.json")

benchmark_app: Final[typer.Typer] = typer.Typer(help="Capture local benchmark evidence.")


@benchmark_app.command("m2")
def benchmark_m2(
    output: Annotated[Path, typer.Option("--output", dir_okay=False)] = DEFAULT_OUTPUT,
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)] = DEFAULT_CONFIG,
    samples: Annotated[int, typer.Option("--samples")] = 5,
    baseline: Annotated[
        Path | None,
        typer.Option("--baseline", exists=True, dir_okay=False),
    ] = None,
    allow_regression: Annotated[bool, typer.Option("--allow-regression")] = False,
    regression_reason: Annotated[str | None, typer.Option("--regression-reason")] = None,
) -> None:
    try:
        report = build_m2_report(
            config=config,
            samples=samples,
            allow_regression=allow_regression,
            regression_reason=regression_reason,
        )
    except BenchmarkError as exc:
        _exit_with_error(exc)
    regressions = regression_messages(report, baseline)
    write_report(output, report)
    if regressions and allow_regression and regression_reason is None:
        _exit_with_error(
            BenchmarkError(
                code="REGRESSION_REASON_REQUIRED",
                message="pass --regression-reason when allowing a regression",
            ),
        )
    if regressions and not allow_regression:
        _exit_with_error(
            BenchmarkError(
                code="PERFORMANCE_REGRESSION",
                message="; ".join(regressions),
            ),
        )
    sys.stdout.write(f"benchmark_output={output}\n")
    sys.stdout.write(f"measurements={len(report.measurements)}\n")
    sys.stdout.write("claim_allowed=false\n")


def _exit_with_error(exc: BenchmarkError) -> NoReturn:
    sys.stderr.write(f"{exc.code}: {exc.message}\n")
    raise typer.Exit(code=1) from exc
