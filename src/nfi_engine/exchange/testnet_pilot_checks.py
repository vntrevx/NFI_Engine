from __future__ import annotations

from typing import assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import TradingMode
from nfi_engine.exchange import get_exchange_profile
from nfi_engine.exchange.credential_requirements import missing_runtime_credential_fields
from nfi_engine.exchange.permissions import ExchangeApiPermissionState
from nfi_engine.strategy.nfi_x7.status import is_x7_native_settings

from .testnet_pilot_models import (
    ControlDraft,
    TestnetPilotControl,
    block_control,
    pass_control,
)


def profile_check(settings: RuntimeSettings) -> TestnetPilotControl:
    profile = get_exchange_profile(settings.exchange.name)
    if profile is None:
        return block_control(
            ControlDraft(
                stage="profile",
                code="TESTNET_PILOT_PROFILE_MISSING",
                message="Exchange has no explicit capability profile.",
                next_action="Add an exchange profile before using the testnet pilot lane.",
            ),
        )
    if not profile.supports_trading_mode(settings.exchange.trading_mode):
        return block_control(
            ControlDraft(
                stage="profile",
                code="TESTNET_PILOT_TRADING_MODE_UNSUPPORTED",
                message="Exchange profile does not support the configured trading mode.",
                next_action="Select a supported mode or add evidence before pilot use.",
            ),
        )
    return pass_control(
        ControlDraft(
            stage="profile",
            code="TESTNET_PILOT_PROFILE_READY",
            message="Exchange profile and trading mode are registered.",
            next_action="Keep profile evidence current before promoting adapters.",
        ),
    )


def live_lock_check(settings: RuntimeSettings) -> TestnetPilotControl:
    if settings.engine.live_trading:
        return block_control(
            ControlDraft(
                stage="live_lock",
                code="TESTNET_PILOT_LIVE_TRADING_BLOCKED",
                message="Real-money live trading remains outside this pilot boundary.",
                next_action="Set engine.live_trading=false and use testnet credentials only.",
            ),
        )
    return pass_control(
        ControlDraft(
            stage="live_lock",
            code="TESTNET_PILOT_LIVE_LOCKED",
            message="Real-money order execution is locked out.",
            next_action="Keep the milestone live lock enabled.",
        ),
    )


def testnet_check(settings: RuntimeSettings) -> TestnetPilotControl:
    if settings.exchange.testnet:
        return pass_control(
            ControlDraft(
                stage="testnet",
                code="TESTNET_PILOT_TESTNET_ENABLED",
                message="Exchange config is scoped to testnet.",
                next_action="Use exchange-issued testnet or sandbox credentials only.",
            ),
        )
    return block_control(
        ControlDraft(
            stage="testnet",
            code="TESTNET_PILOT_TESTNET_REQUIRED",
            message="Pilot lane requires exchange.testnet=true.",
            next_action="Regenerate config with --testnet before any pilot run.",
        ),
    )


def credential_check(settings: RuntimeSettings) -> TestnetPilotControl:
    missing = missing_runtime_credential_fields(settings)
    if not missing:
        return pass_control(
            ControlDraft(
                stage="credentials",
                code="TESTNET_PILOT_CREDENTIALS_PRESENT",
                message="Required exchange credential fields are present.",
                next_action="Verify the keys against the exchange testnet before submission.",
            ),
        )
    return block_control(
        ControlDraft(
            stage="credentials",
            code="TESTNET_PILOT_CREDENTIALS_MISSING",
            message=f"Missing required credential fields: {', '.join(missing)}.",
            next_action="Load a 0600 credentials file or env overrides with testnet keys.",
        ),
    )


def permission_check(settings: RuntimeSettings) -> TestnetPilotControl:
    gaps = _permission_gaps(settings)
    if not gaps:
        return pass_control(
            ControlDraft(
                stage="permissions",
                code="TESTNET_PILOT_PERMISSIONS_HARDENED",
                message="Read/trade permissions are explicit and withdrawal is disabled.",
                next_action="Keep withdrawal disabled and rotate keys after pilot testing.",
            ),
        )
    return block_control(
        ControlDraft(
            stage="permissions",
            code="TESTNET_PILOT_PERMISSIONS_INCOMPLETE",
            message=f"Permission hardening gaps: {', '.join(gaps)}.",
            next_action="Confirm read/trade/futures/IP permissions and disable withdrawal.",
        ),
    )


def strategy_check(settings: RuntimeSettings) -> TestnetPilotControl:
    if is_x7_native_settings(settings):
        return pass_control(
            ControlDraft(
                stage="strategy",
                code="TESTNET_PILOT_X7_NATIVE_READY",
                message="Native X7 strategy runtime is selected.",
                next_action="Keep X7 evidence in paper/testnet before any pilot run.",
            ),
        )
    return block_control(
        ControlDraft(
            stage="strategy",
            code="TESTNET_PILOT_X7_NATIVE_REQUIRED",
            message="Testnet pilot requires the native X7 strategy runtime.",
            next_action="Select nfi_engine.strategy.nfi_x7:X7NativeStrategy.",
        ),
    )


def _permission_gaps(settings: RuntimeSettings) -> tuple[str, ...]:
    gaps: list[str] = []
    if settings.exchange.permission_read is not ExchangeApiPermissionState.ENABLED:
        gaps.append("read")
    if settings.exchange.permission_trade is not ExchangeApiPermissionState.ENABLED:
        gaps.append("trade")
    if (
        settings.exchange.trading_mode is TradingMode.FUTURES
        and settings.exchange.permission_futures is not ExchangeApiPermissionState.ENABLED
    ):
        gaps.append("futures")
    match settings.exchange.permission_withdrawal:
        case ExchangeApiPermissionState.DISABLED | ExchangeApiPermissionState.NOT_APPLICABLE:
            pass
        case ExchangeApiPermissionState.ENABLED:
            gaps.append("withdrawal_enabled")
        case ExchangeApiPermissionState.UNKNOWN:
            gaps.append("withdrawal_unknown")
        case unreachable:
            assert_never(unreachable)
    if settings.exchange.permission_ip_allowlist is not ExchangeApiPermissionState.ENABLED:
        gaps.append("ip_allowlist")
    return tuple(gaps)
