from __future__ import annotations

from decimal import Decimal
from typing import assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import TradingMode
from nfi_engine.exchange.credential_requirements import missing_runtime_credential_fields
from nfi_engine.exchange.permissions import ExchangeApiPermissionState
from nfi_engine.preflight.models import PreflightCheck, PreflightCode, PreflightStatus
from nfi_engine.strategy.nfi_x7.coverage import build_x7_coverage_report
from nfi_engine.strategy.nfi_x7.status import is_x7_native_settings

ZERO: Decimal = Decimal(0)


def live_readiness_checks(settings: RuntimeSettings) -> tuple[PreflightCheck, ...]:
    if not settings.engine.live_trading:
        return ()
    return (
        _credential_check(settings),
        _permission_hardening_check(settings),
        _reconciliation_hardening_check(settings),
        _circuit_breaker_hardening_check(settings),
        _strategy_hardening_check(settings),
    )


def _credential_check(settings: RuntimeSettings) -> PreflightCheck:
    missing = missing_runtime_credential_fields(settings)
    if not missing:
        return _check(
            PreflightCode.LIVE_EXCHANGE_CREDENTIALS,
            PreflightStatus.PASS,
            "live exchange credentials are present",
        )
    return _check(
        PreflightCode.LIVE_EXCHANGE_CREDENTIALS,
        PreflightStatus.BLOCK,
        f"live mode requires exchange credential fields: {','.join(missing)}",
    )


def _permission_hardening_check(settings: RuntimeSettings) -> PreflightCheck:
    missing: list[str] = []
    if settings.exchange.permission_read is not ExchangeApiPermissionState.ENABLED:
        missing.append("read")
    if settings.exchange.permission_trade is not ExchangeApiPermissionState.ENABLED:
        missing.append("trade")
    missing.extend(_futures_permission_gaps(settings))
    missing.extend(_withdrawal_permission_gaps(settings.exchange.permission_withdrawal))
    if settings.exchange.permission_ip_allowlist is not ExchangeApiPermissionState.ENABLED:
        missing.append("ip_allowlist")
    if missing:
        return _check(
            PreflightCode.LIVE_PERMISSION_HARDENING,
            PreflightStatus.BLOCK,
            f"live API permission hardening incomplete: {','.join(missing)}",
        )
    return _check(
        PreflightCode.LIVE_PERMISSION_HARDENING,
        PreflightStatus.PASS,
        "live API permissions are hardened",
    )


def _futures_permission_gaps(settings: RuntimeSettings) -> tuple[str, ...]:
    match settings.exchange.trading_mode:
        case TradingMode.SPOT:
            return ()
        case TradingMode.FUTURES:
            if settings.exchange.permission_futures is ExchangeApiPermissionState.ENABLED:
                return ()
            return ("futures",)
        case unreachable:
            assert_never(unreachable)


def _withdrawal_permission_gaps(
    withdrawal: ExchangeApiPermissionState,
) -> tuple[str, ...]:
    match withdrawal:
        case ExchangeApiPermissionState.DISABLED | ExchangeApiPermissionState.NOT_APPLICABLE:
            return ()
        case ExchangeApiPermissionState.ENABLED:
            return ("withdrawal_enabled",)
        case ExchangeApiPermissionState.UNKNOWN:
            return ("withdrawal_unknown",)
        case unreachable:
            assert_never(unreachable)


def _reconciliation_hardening_check(settings: RuntimeSettings) -> PreflightCheck:
    if settings.reconciliation.required and _present(settings.reconciliation.fixture_path):
        return _check(
            PreflightCode.LIVE_RECONCILIATION_HARDENING,
            PreflightStatus.PASS,
            "startup reconciliation is required for live intent",
        )
    return _check(
        PreflightCode.LIVE_RECONCILIATION_HARDENING,
        PreflightStatus.BLOCK,
        "live intent requires startup reconciliation with a fixture_path",
    )


def _circuit_breaker_hardening_check(settings: RuntimeSettings) -> PreflightCheck:
    circuit = settings.circuit_breakers
    gaps: list[str] = []
    if not circuit.enabled:
        gaps.append("enabled")
    if circuit.max_daily_loss_usdt <= ZERO:
        gaps.append("max_daily_loss_usdt")
    if circuit.max_drawdown_pct <= ZERO:
        gaps.append("max_drawdown_pct")
    if circuit.max_stale_seconds <= 0:
        gaps.append("max_stale_seconds")
    if not _present(circuit.manual_halt_file):
        gaps.append("manual_halt_file")
    if gaps:
        return _check(
            PreflightCode.LIVE_CIRCUIT_BREAKER_HARDENING,
            PreflightStatus.BLOCK,
            f"live circuit breaker hardening incomplete: {','.join(gaps)}",
        )
    return _check(
        PreflightCode.LIVE_CIRCUIT_BREAKER_HARDENING,
        PreflightStatus.PASS,
        "live circuit breaker hardening is configured",
    )


def _strategy_hardening_check(settings: RuntimeSettings) -> PreflightCheck:
    if not is_x7_native_settings(settings):
        return _check(
            PreflightCode.LIVE_STRATEGY_HARDENING,
            PreflightStatus.BLOCK,
            "live intent requires X7NativeStrategy semantic coverage",
        )
    coverage = build_x7_coverage_report()
    if coverage.is_full_semantic_coverage:
        return _check(
            PreflightCode.LIVE_STRATEGY_HARDENING,
            PreflightStatus.PASS,
            "X7 semantic coverage evidence is complete",
        )
    return _check(
        PreflightCode.LIVE_STRATEGY_HARDENING,
        PreflightStatus.BLOCK,
        f"X7 semantic coverage pending: {','.join(coverage.pending_modules)}",
    )


def _present(value: str | None) -> bool:
    return value is not None and value.strip() != ""


def _check(
    code: PreflightCode,
    status: PreflightStatus,
    message: str,
) -> PreflightCheck:
    return PreflightCheck(code=code, status=status, message=message)
