from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, NoReturn

import anyio
import typer

from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.exchange.testnet_execution import (
    TestnetExecutionReport,
    run_testnet_execution_dry_run,
)
from nfi_engine.exchange.testnet_pilot_models import TestnetPilotReport


def run_testnet_execute_cli(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    json_output: Annotated[bool, typer.Option("--json/--text")] = False,
) -> None:
    try:
        settings = load_runtime_settings(config)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    report = anyio.run(run_testnet_execution_dry_run, settings)
    if json_output:
        sys.stdout.write(report.model_dump_json(indent=2) + "\n")
        return
    write_testnet_execution_report(report)


def write_testnet_pilot_report(report: TestnetPilotReport) -> None:
    sys.stdout.write(f"exchange={report.exchange}\n")
    sys.stdout.write(f"trading_mode={report.trading_mode}\n")
    sys.stdout.write(f"testnet={str(report.testnet).lower()}\n")
    sys.stdout.write(f"pilot_ready={str(report.pilot_ready).lower()}\n")
    sys.stdout.write("live_money_orders_enabled=false\n")
    sys.stdout.write(f"client_order_id={report.sample_client_order_id}\n")
    sys.stdout.write(
        f"dry_run_preview_required={str(report.execution_plan.dry_run_preview_required).lower()}\n",
    )
    sys.stdout.write(
        f"kill_switch_required={str(report.execution_plan.kill_switch_required).lower()}\n",
    )
    sys.stdout.write(
        f"reconciliation_required={str(report.execution_plan.reconciliation_required).lower()}\n",
    )
    sys.stdout.write(f"blockers={','.join(report.blockers) if report.blockers else 'none'}\n")
    for signal in report.execution_plan.dashboard_signals:
        sys.stdout.write(f"dashboard_signal={signal}\n")
    for control in report.controls:
        sys.stdout.write(
            f"control={control.stage}\tstatus={control.status.value}\tcode={control.code}\n",
        )
    for transition in report.execution_plan.transitions:
        transition_label = (
            f"transition={transition.from_state.value}->{transition.to_state.value}"
            f"\ttrigger={transition.trigger}\tidempotent={str(transition.idempotent).lower()}\n"
        )
        sys.stdout.write(transition_label)


def write_testnet_execution_report(report: TestnetExecutionReport) -> None:
    sys.stdout.write(f"exchange={report.exchange}\n")
    sys.stdout.write(f"trading_mode={report.trading_mode}\n")
    sys.stdout.write(f"testnet={str(report.testnet).lower()}\n")
    sys.stdout.write(f"execution_ready={str(report.execution_ready).lower()}\n")
    sys.stdout.write("live_money_orders_enabled=false\n")
    sys.stdout.write(f"live_exchange_observed={str(report.live_exchange_observed).lower()}\n")
    sys.stdout.write(f"client_order_id={report.client_order_id}\n")
    sys.stdout.write(f"submitted_order_id={report.submitted_order_id or 'none'}\n")
    adapter_state = report.adapter_order_state.value if report.adapter_order_state else "none"
    final_state = report.final_state.value if report.final_state else "none"
    sys.stdout.write(f"adapter_order_state={adapter_state}\n")
    sys.stdout.write(f"final_state={final_state}\n")
    sys.stdout.write(f"blockers={','.join(report.blockers) if report.blockers else 'none'}\n")
    for event in report.events:
        sys.stdout.write(f"event={event.state.value}\tsource={event.source.value}\n")


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
