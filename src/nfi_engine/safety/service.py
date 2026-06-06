from __future__ import annotations

from decimal import Decimal
from typing import assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.safety.errors import SafetyError, SafetyErrorCode
from nfi_engine.safety.models import SafetyReport, SafetyWarning, SafetyWarningCode

ONE_X: Decimal = Decimal(1)


def build_safety_report(settings: RuntimeSettings) -> SafetyReport:
    warnings: list[SafetyWarning] = []
    match settings.exchange.trading_mode:
        case TradingMode.SPOT:
            return SafetyReport(warnings=())
        case TradingMode.FUTURES:
            warnings.append(
                SafetyWarning(
                    code=SafetyWarningCode.FUTURES_ACCOUNT_EXCLUSIVITY,
                    message="futures mode assumes this bot is the only account operator",
                ),
            )
            warnings.extend(_leverage_warnings(settings))
            return SafetyReport(warnings=tuple(warnings))
        case unreachable:
            assert_never(unreachable)


def enforce_milestone_live_trading_scope(settings: RuntimeSettings) -> None:
    if settings.engine.live_trading:
        raise SafetyError(
            code=SafetyErrorCode.LIVE_TRADING_OUT_OF_SCOPE,
            message="milestone 1 supports simulator, paper, and testnet flows only",
        )


def _leverage_warnings(settings: RuntimeSettings) -> tuple[SafetyWarning, ...]:
    warnings: list[SafetyWarning] = []
    if settings.risk.leverage > ONE_X:
        warnings.append(
            SafetyWarning(
                code=SafetyWarningCode.LEVERAGE_RISK,
                message="leverage greater than 1x increases liquidation risk",
            ),
        )
    match settings.exchange.margin_mode:
        case MarginMode.CROSS:
            warnings.append(
                SafetyWarning(
                    code=SafetyWarningCode.CROSS_MARGIN_ACCOUNT_RISK,
                    message="cross margin can share liquidation risk across positions",
                ),
            )
        case MarginMode.ISOLATED | None:
            return tuple(warnings)
        case unreachable:
            assert_never(unreachable)
    return tuple(warnings)
