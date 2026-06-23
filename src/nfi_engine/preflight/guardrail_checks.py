from __future__ import annotations

from decimal import Decimal
from typing import Final, assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import TradingMode
from nfi_engine.exchange.permissions import audit_exchange_api_permissions
from nfi_engine.preflight.models import PreflightCheck, PreflightCode, PreflightStatus
from nfi_engine.risk.profiles import get_risk_profile

FUTURES_LEVERAGE_CEILING: Final = Decimal(10)


def runtime_guardrail_checks(settings: RuntimeSettings) -> tuple[PreflightCheck, ...]:
    return (
        futures_leverage_check(settings),
        exchange_permission_audit_check(settings),
        risk_profile_guardrail_check(settings),
    )


def futures_leverage_check(settings: RuntimeSettings) -> PreflightCheck:
    match settings.exchange.trading_mode:
        case TradingMode.SPOT:
            return _check(
                PreflightCode.FUTURES_LEVERAGE_INVALID,
                PreflightStatus.PASS,
                "spot mode",
            )
        case TradingMode.FUTURES:
            pass
        case unreachable:
            assert_never(unreachable)
    if (
        settings.risk.leverage > settings.risk.max_leverage
        or settings.risk.leverage > FUTURES_LEVERAGE_CEILING
    ):
        return _check(
            PreflightCode.FUTURES_LEVERAGE_INVALID,
            PreflightStatus.BLOCK,
            "futures leverage exceeds readiness ceiling",
        )
    return _check(
        PreflightCode.FUTURES_LEVERAGE_INVALID,
        PreflightStatus.PASS,
        "futures leverage guardrails passed",
    )


def exchange_permission_audit_check(settings: RuntimeSettings) -> PreflightCheck:
    audit = audit_exchange_api_permissions(
        read=settings.exchange.permission_read,
        trade=settings.exchange.permission_trade,
        futures=settings.exchange.permission_futures,
        withdrawal=settings.exchange.permission_withdrawal,
        ip_allowlist=settings.exchange.permission_ip_allowlist,
    )
    if audit.live_blocking_codes:
        status = PreflightStatus.BLOCK if settings.engine.live_trading else PreflightStatus.WARN
        return _check(PreflightCode.EXCHANGE_PERMISSION_AUDIT, status, audit.summary)
    if audit.diagnostic_codes:
        return _check(PreflightCode.EXCHANGE_PERMISSION_AUDIT, PreflightStatus.WARN, audit.summary)
    return _check(PreflightCode.EXCHANGE_PERMISSION_AUDIT, PreflightStatus.PASS, audit.summary)


def risk_profile_guardrail_check(settings: RuntimeSettings) -> PreflightCheck:
    profile = get_risk_profile(settings.risk.risk_profile)
    if profile.requires_confirmation and not settings.risk.expert_risk_confirmed:
        return _check(
            PreflightCode.RISK_PROFILE_GUARDRAILS,
            PreflightStatus.BLOCK,
            "expert risk profile requires explicit confirmation",
        )
    if (
        settings.risk.leverage > profile.max_leverage
        or settings.risk.max_open_trades > profile.max_open_trades
        or settings.risk.max_daily_loss_pct > profile.max_daily_loss_pct
    ):
        return _check(
            PreflightCode.RISK_PROFILE_GUARDRAILS,
            PreflightStatus.BLOCK,
            f"{profile.name.value} risk profile guardrails exceeded",
        )
    return _check(
        PreflightCode.RISK_PROFILE_GUARDRAILS,
        PreflightStatus.PASS,
        f"{profile.name.value} risk profile guardrails passed",
    )


def _check(
    code: PreflightCode,
    status: PreflightStatus,
    message: str,
) -> PreflightCheck:
    return PreflightCheck(code=code, status=status, message=message)
