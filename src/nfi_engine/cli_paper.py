from __future__ import annotations

import json
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Final, NoReturn

import anyio
import typer

from nfi_engine.config import ConfigLoadError, RuntimeSettings, load_runtime_settings
from nfi_engine.events import EventCode, EventSeverity, JsonlEventSink, TradingEvent
from nfi_engine.observability import new_correlation_id
from nfi_engine.paper import PaperError, PaperRunRequest, load_paper_ticks, run_paper
from nfi_engine.safety import SafetyError
from nfi_engine.strategy import (
    FreqtradeStrategyAdapter,
    StrategyContractError,
    load_freqtrade_strategy,
)
from nfi_engine.strategy.timeline import StrategyTimeline, timeline_to_payload

DEMO_STRATEGY_MODULE: Final = "nfi_engine.strategy.demo:AdapterSmokeStrategy"


def paper_run(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    ticks: Annotated[Path, typer.Option("--ticks", exists=True, dir_okay=False)],
    max_events: Annotated[int, typer.Option("--max-events", min=1)],
    events: Annotated[Path | None, typer.Option("--events", dir_okay=False)] = None,
    timeline_output: Annotated[
        Path | None,
        typer.Option("--timeline-output", dir_okay=False),
    ] = None,
) -> None:
    try:
        settings = load_runtime_settings(config)
        paper_ticks = load_paper_ticks(ticks, settings.exchange.trading_mode)
        with tempfile.TemporaryDirectory(prefix="nfi-paper-") as temp_dir:
            database_url = f"sqlite+aiosqlite:///{Path(temp_dir) / 'paper.sqlite'}"
            result = anyio.run(
                run_paper,
                PaperRunRequest(
                    settings=settings,
                    ticks=paper_ticks,
                    max_events=max_events,
                    database_url=database_url,
                    strategy_adapter=_paper_strategy_adapter(settings),
                ),
            )
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except SafetyError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except StrategyContractError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except PaperError as exc:
        _exit_with_error(exc.code.value, exc.message)
    if events is not None:
        _write_paper_events(events, processed_events=result.processed_events)
    if timeline_output is not None:
        _write_timeline(timeline_output, result.timeline)
    sys.stdout.write(f"processed_events={result.processed_events}\n")
    sys.stdout.write(f"created_trades={result.created_trades}\n")
    sys.stdout.write(f"live_orders={str(result.live_orders).lower()}\n")
    sys.stdout.write(f"trading_halted={str(result.trading_halted).lower()}\n")
    sys.stdout.write(f"breaker={result.halted_breaker or 'none'}\n")
    sys.stdout.write(f"new_orders_blocked={str(result.new_orders_blocked).lower()}\n")
    sys.stdout.write(f"state={result.final_state.value}\n")


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)


def _write_paper_events(path: Path, *, processed_events: int) -> None:
    correlation_id = new_correlation_id()
    now = datetime.now(UTC)
    JsonlEventSink(path).write_many(
        (
            TradingEvent(
                at=now,
                severity=EventSeverity.INFO,
                code=EventCode.BOT_STARTED,
                correlation_id=correlation_id,
                command="paper-run",
                route=None,
                safe_summary="paper bot started",
                report_hint="attach this event file and paper-run command output",
            ),
            TradingEvent(
                at=datetime.now(UTC),
                severity=EventSeverity.INFO,
                code=EventCode.BOT_STOPPED,
                correlation_id=correlation_id,
                command="paper-run",
                route=None,
                safe_summary=f"paper bot stopped after {processed_events} events",
                report_hint="attach this event file and paper-run command output",
            ),
        ),
    )


def _write_timeline(path: Path, timeline: StrategyTimeline) -> None:
    path.write_text(
        json.dumps(timeline_to_payload(timeline), indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _paper_strategy_adapter(settings: RuntimeSettings) -> FreqtradeStrategyAdapter | None:
    if settings.strategy.module == DEMO_STRATEGY_MODULE:
        return None
    strategy = load_freqtrade_strategy(settings.strategy.module)
    return FreqtradeStrategyAdapter.from_strategy(strategy)
