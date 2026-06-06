from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.data import DataLoadError, load_candle_batch

data_app: Final[typer.Typer] = typer.Typer(help="Inspect and validate candle data.")


@data_app.command("inspect")
def inspect_candles(
    candles: Annotated[Path, typer.Option("--candles", exists=True, dir_okay=False)],
) -> None:
    try:
        batch = load_candle_batch(candles)
    except DataLoadError as exc:
        _exit_with_data_error(exc)
    first_candle = batch.candles[0]
    last_candle = batch.candles[-1]
    sys.stdout.write(
        "\n".join(
            (
                f"rows={len(batch.candles)}",
                f"pair={batch.pair.normalized}",
                f"timeframe={batch.timeframe}",
                f"first_opened_at={first_candle.opened_at.isoformat()}",
                f"last_opened_at={last_candle.opened_at.isoformat()}",
            ),
        ),
    )
    sys.stdout.write("\n")


def _exit_with_data_error(exc: DataLoadError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc
