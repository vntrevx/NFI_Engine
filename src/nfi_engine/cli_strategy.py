from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.strategy import (
    FreqtradeStrategyAdapter,
    StrategyContractError,
    load_freqtrade_strategy,
)

strategy_app: Final[typer.Typer] = typer.Typer(help="Inspect strategy adapter contracts.")


@strategy_app.command("inspect")
def inspect_strategy(
    strategy: Annotated[str, typer.Option("--strategy")],
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
) -> None:
    try:
        load_runtime_settings(config)
        loaded_strategy = load_freqtrade_strategy(strategy)
        inspection = FreqtradeStrategyAdapter.from_strategy(loaded_strategy).inspect()
    except ConfigLoadError as exc:
        _exit_with_config_error(exc)
    except StrategyContractError as exc:
        _exit_with_strategy_error(exc)
    sys.stdout.write(
        "\n".join(
            (
                f"strategy_name={inspection.name}",
                f"can_short={str(inspection.can_short).lower()}",
                f"timeframe={inspection.timeframe}",
                f"callbacks={_format_callbacks(inspection.detected_callbacks)}",
            ),
        ),
    )
    sys.stdout.write("\n")


def _format_callbacks(callbacks: tuple[str, ...]) -> str:
    if len(callbacks) == 0:
        return "none"
    return ",".join(callbacks)


def _exit_with_config_error(exc: ConfigLoadError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc


def _exit_with_strategy_error(exc: StrategyContractError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc
