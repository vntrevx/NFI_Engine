from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.pairlist import validate_pairlist

pairlist_app: Final[typer.Typer] = typer.Typer(help="Validate pairlist market eligibility.")


@pairlist_app.command("validate")
def validate_pairlist_cli(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option("--output")],
) -> None:
    try:
        settings = load_runtime_settings(config)
        result = validate_pairlist(settings=settings)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(result.model_dump_json(indent=2), encoding="utf-8")
    sys.stdout.write("pairlist_validated=true\n")
    sys.stdout.write(f"accepted_count={len(result.accepted_pairs)}\n")
    sys.stdout.write(f"rejected_count={len(result.rejected_pairs)}\n")


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
