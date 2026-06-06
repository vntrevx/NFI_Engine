from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer

from nfi_engine.circuit_breakers import (
    CircuitBreakerDecision,
    CircuitBreakerSnapshot,
    evaluate_circuit_breakers,
    policy_from_runtime,
)
from nfi_engine.config import ConfigLoadError, load_runtime_settings

circuit_breaker_app: Final[typer.Typer] = typer.Typer(help="Inspect circuit breaker decisions.")
DEFAULT_EQUITY: Final = Decimal(1000)


@circuit_breaker_app.command("simulate")
def simulate(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
) -> None:
    try:
        settings = load_runtime_settings(config)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    policy = policy_from_runtime(settings)
    now = datetime.now(UTC)
    decision = evaluate_circuit_breakers(
        policy=policy,
        snapshot=CircuitBreakerSnapshot(
            realized_pnl_today=-(policy.max_daily_loss_usdt + Decimal(1)),
            equity_start=DEFAULT_EQUITY,
            equity_current=DEFAULT_EQUITY,
            consecutive_losses=0,
            latest_tick_at=now,
            current_time=now,
            api_error_count=0,
            observed_slippage_pct=Decimal(0),
            funding_rate=Decimal(0),
            manual_halt=False,
            rejected_order_count=0,
        ),
    )
    sys.stdout.write(f"trading_halted={str(decision.trading_halted).lower()}\n")
    sys.stdout.write(f"new_orders_blocked={str(decision.new_orders_blocked).lower()}\n")
    sys.stdout.write(f"emergency_exit={str(decision.emergency_exit).lower()}\n")
    sys.stdout.write(f"breaker={_first_breaker(decision)}\n")


def _first_breaker(decision: CircuitBreakerDecision) -> str:
    if len(decision.triggered) == 0:
        return "none"
    return decision.triggered[0].kind.value


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
