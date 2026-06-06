from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, NoReturn

import typer

from nfi_engine.backtest import (
    BacktestError,
    BacktestRequest,
    result_to_json_payload,
    run_backtest,
)
from nfi_engine.backtest.config import (
    config_digest,
    default_candle_path,
    filter_timerange,
    parse_timerange,
    simulation_settings_from_runtime,
)
from nfi_engine.backtest.metadata import (
    ReproducibilityMetadataRequest,
    build_reproducibility_metadata,
)
from nfi_engine.backtest.models import SimulatorScenarioMetadata
from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.data import DataLoadError, load_candle_batch
from nfi_engine.exchange.fill_scenarios import load_fill_scenario
from nfi_engine.strategy import (
    FreqtradeStrategyAdapter,
    StrategyContractError,
    load_freqtrade_strategy,
)


def backtest(  # noqa: PLR0913
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    timerange: Annotated[str | None, typer.Option("--timerange")] = None,
    output: Annotated[Path | None, typer.Option("--output", dir_okay=False)] = None,
    candles: Annotated[Path | None, typer.Option("--candles", dir_okay=False)] = None,
    simulator_scenario: Annotated[
        Path | None,
        typer.Option("--simulator-scenario", exists=True, dir_okay=False),
    ] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        settings = load_runtime_settings(config)
        candle_path = default_candle_path(settings) if candles is None else candles
        candle_batch = filter_timerange(load_candle_batch(candle_path), parse_timerange(timerange))
        strategy = load_freqtrade_strategy(settings.strategy.module)
        adapter = FreqtradeStrategyAdapter.from_strategy(strategy)
        metadata = build_reproducibility_metadata(
            ReproducibilityMetadataRequest(
                config_path=config,
                candle_path=candle_path,
                strategy=strategy,
                command_args=_command_args(
                    config=config,
                    timerange=timerange,
                    output=output,
                    candles=candles,
                    simulator_scenario=simulator_scenario,
                    json_output=json_output,
                ),
                simulator=_simulator_metadata(simulator_scenario),
            ),
        )
        result = run_backtest(
            BacktestRequest(
                candles=candle_batch,
                adapter=adapter,
                settings=simulation_settings_from_runtime(settings),
                config_digest=config_digest(settings, timerange=timerange),
                strategy_name=type(strategy).__name__,
                metadata=metadata,
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
    payload = result_to_json_payload(result)
    if output is not None:
        output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if json_output:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return
    sys.stdout.write(f"summary.total_trades={result.summary.total_trades}\n")
    sys.stdout.write(f"summary.total_profit={result.summary.total_profit}\n")


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)


def _command_args(  # noqa: PLR0913
    *,
    config: Path,
    timerange: str | None,
    output: Path | None,
    candles: Path | None,
    simulator_scenario: Path | None,
    json_output: bool,
) -> tuple[str, ...]:
    args = ("backtest", "--config", str(config))
    if timerange is not None:
        args += ("--timerange", timerange)
    if output is not None:
        args += ("--output", str(output))
    if candles is not None:
        args += ("--candles", str(candles))
    if simulator_scenario is not None:
        args += ("--simulator-scenario", str(simulator_scenario))
    if json_output:
        args += ("--json",)
    return args


def _simulator_metadata(path: Path | None) -> SimulatorScenarioMetadata | None:
    if path is None:
        return None
    scenario = load_fill_scenario(path)
    return SimulatorScenarioMetadata(scenario_hash=scenario.scenario_hash, seed=scenario.seed)
