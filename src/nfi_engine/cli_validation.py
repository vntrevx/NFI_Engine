from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.backtest import BacktestError
from nfi_engine.backtest.config import (
    default_candle_path,
    filter_timerange,
    parse_timerange,
    simulation_settings_from_runtime,
)
from nfi_engine.backtest.metadata import (
    ReproducibilityMetadataRequest,
    build_reproducibility_metadata,
)
from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.data import DataLoadError, load_candle_batch
from nfi_engine.strategy import (
    FreqtradeStrategyAdapter,
    StrategyContractError,
    load_freqtrade_strategy,
)
from nfi_engine.validation import (
    ValidationError,
    WalkForwardRequest,
    run_walk_forward,
    walk_forward_to_json_payload,
)

validate_app: Final[typer.Typer] = typer.Typer(help="Run validation workflows.")


@validate_app.command("walk-forward")
def walk_forward(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    splits: Annotated[int, typer.Option("--splits", min=1)],
    output: Annotated[Path | None, typer.Option("--output", dir_okay=False)] = None,
    timerange: Annotated[str | None, typer.Option("--timerange")] = None,
    candles: Annotated[Path | None, typer.Option("--candles", dir_okay=False)] = None,
) -> None:
    try:
        settings = load_runtime_settings(config)
        candle_path = default_candle_path(settings) if candles is None else candles
        candle_batch = filter_timerange(load_candle_batch(candle_path), parse_timerange(timerange))
        strategy = load_freqtrade_strategy(settings.strategy.module)
        metadata = build_reproducibility_metadata(
            ReproducibilityMetadataRequest(
                config_path=config,
                candle_path=candle_path,
                strategy=strategy,
                command_args=_command_args(
                    config=config,
                    splits=splits,
                    output=output,
                    timerange=timerange,
                    candles=candles,
                ),
            ),
        )
        result = run_walk_forward(
            WalkForwardRequest(
                candles=candle_batch,
                adapter=FreqtradeStrategyAdapter.from_strategy(strategy),
                settings=simulation_settings_from_runtime(settings),
                strategy_name=type(strategy).__name__,
                metadata=metadata,
                split_count=splits,
            ),
        )
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except DataLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except StrategyContractError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except BacktestError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except ValidationError as exc:
        _exit_with_error(exc.code.value, exc.message)
    payload = walk_forward_to_json_payload(result)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output is not None:
        output.write_text(encoded, encoding="utf-8")
    else:
        sys.stdout.write(encoded)
    sys.stdout.write(f"walk_forward.splits={len(result.splits)}\n")


def _command_args(
    *,
    config: Path,
    splits: int,
    output: Path | None,
    timerange: str | None,
    candles: Path | None,
) -> tuple[str, ...]:
    args = ("validate", "walk-forward", "--config", str(config), "--splits", str(splits))
    if output is not None:
        args += ("--output", str(output))
    if timerange is not None:
        args += ("--timerange", timerange)
    if candles is not None:
        args += ("--candles", str(candles))
    return args


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
