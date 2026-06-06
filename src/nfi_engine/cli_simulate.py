from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated, Final

import typer

from nfi_engine.exchange.fill_scenarios import (
    fill_result_payload,
    load_fill_scenario,
    simulate_fill_scenario,
)

simulate_app: Final[typer.Typer] = typer.Typer(help="Run deterministic simulator scenarios.")


@simulate_app.command("fills")
def fills(
    scenario: Annotated[Path, typer.Option("--scenario", exists=True, dir_okay=False)],
    output: Annotated[Path, typer.Option("--output", dir_okay=False)],
) -> None:
    result = simulate_fill_scenario(load_fill_scenario(scenario))
    payload = fill_result_payload(result)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    sys.stdout.write(f"scenario_hash={result.scenario_hash}\n")
    sys.stdout.write(f"seed={result.seed}\n")
    sys.stdout.write(f"order_state={result.order_state}\n")
    sys.stdout.write(f"events={','.join(result.events)}\n")
