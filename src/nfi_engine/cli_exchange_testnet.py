from __future__ import annotations

import sys

from nfi_engine.exchange.testnet_pilot_models import TestnetPilotReport


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
