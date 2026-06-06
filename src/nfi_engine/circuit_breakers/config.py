from __future__ import annotations

from pathlib import Path

from nfi_engine.circuit_breakers.models import CircuitBreakerPolicy
from nfi_engine.config import RuntimeSettings


def policy_from_runtime(settings: RuntimeSettings) -> CircuitBreakerPolicy:
    circuit = settings.circuit_breakers
    return CircuitBreakerPolicy(
        enabled=circuit.enabled,
        max_daily_loss_usdt=circuit.max_daily_loss_usdt,
        max_drawdown_pct=circuit.max_drawdown_pct,
        max_consecutive_losses=circuit.max_consecutive_losses,
        max_stale_seconds=circuit.max_stale_seconds,
        max_api_errors=circuit.max_api_errors,
        max_slippage_pct=circuit.max_slippage_pct,
        max_abs_funding_rate=circuit.max_abs_funding_rate,
        manual_halt=circuit.manual_halt or _halt_file_exists(circuit.manual_halt_file),
        max_rejected_orders=circuit.max_rejected_orders,
        emergency_exit_enabled=circuit.emergency_exit_enabled,
    )


def _halt_file_exists(raw_path: str | None) -> bool:
    if raw_path is None:
        return False
    if raw_path.strip() == "":
        return False
    return Path(raw_path).exists()
