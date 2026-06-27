from __future__ import annotations

from dataclasses import dataclass
from typing import assert_never

from nfi_engine.config.models import RuntimeSettings
from nfi_engine.domain import TradingMode
from nfi_engine.exchange.capability_models import (
    ExchangeCapabilityProfile,
    ExchangeSupportLevel,
)
from nfi_engine.exchange.credential_requirements import (
    missing_runtime_credential_fields,
    required_runtime_credential_fields,
)
from nfi_engine.exchange.discovery import ExchangeCapabilityReport
from nfi_engine.exchange.official_requirements import get_official_requirement
from nfi_engine.exchange.runtime_verification_check_builders import (
    block_check,
    manual_check,
    not_required_check,
    pass_check,
)
from nfi_engine.exchange.runtime_verification_environment import test_environment_check
from nfi_engine.exchange.runtime_verification_evidence import (
    ORDER_LANE_EVIDENCE,
    READ_ONLY_BALANCE_EVIDENCE,
)
from nfi_engine.exchange.runtime_verification_models import (
    ExchangeRuntimeCheck,
)


@dataclass(frozen=True, slots=True)
class RuntimeVerificationTarget:
    requested_exchange: str
    trading_mode: TradingMode
    settings: RuntimeSettings | None


def build_runtime_checks(
    *,
    target: RuntimeVerificationTarget,
    capability: ExchangeCapabilityReport,
) -> tuple[ExchangeRuntimeCheck, ...]:
    return (
        _profile_check(capability),
        _official_requirements_check(capability.profile),
        _trading_mode_check(capability),
        _credential_check(target=target, profile=capability.profile),
        test_environment_check(
            settings=target.settings,
            profile=capability.profile,
            trading_mode=target.trading_mode,
        ),
        _read_only_balance_check(profile=capability.profile, trading_mode=target.trading_mode),
        _order_lane_check(profile=capability.profile, trading_mode=target.trading_mode),
    )


def _profile_check(capability: ExchangeCapabilityReport) -> ExchangeRuntimeCheck:
    match capability.profile.support_level:
        case ExchangeSupportLevel.VERIFIED | ExchangeSupportLevel.CANDIDATE:
            return pass_check(
                stage="profile",
                code="RUNTIME_PROFILE_REGISTERED",
                message="Exchange has an explicit registry profile.",
            )
        case ExchangeSupportLevel.GENERIC_UNVERIFIED:
            return block_check(
                stage="profile",
                code="RUNTIME_PROFILE_UNVERIFIED",
                message="Exchange is report-only and has no explicit runtime profile.",
                next_action="Add an explicit exchange profile before runtime verification.",
            )
        case unreachable:
            assert_never(unreachable)


def _official_requirements_check(profile: ExchangeCapabilityProfile) -> ExchangeRuntimeCheck:
    if profile.exchange_id == "simulator":
        return not_required_check(
            stage="official_requirements",
            code="OFFICIAL_REQUIREMENTS_NOT_REQUIRED",
            message="Simulator does not require external exchange documentation.",
        )
    if get_official_requirement(profile.exchange_id) is not None:
        return pass_check(
            stage="official_requirements",
            code="OFFICIAL_REQUIREMENTS_CHECKED",
            message="Official exchange requirements are encoded.",
        )
    return block_check(
        stage="official_requirements",
        code="OFFICIAL_REQUIREMENTS_MISSING",
        message="Official exchange requirements are not encoded.",
        next_action="Research official exchange docs and add a requirement profile.",
    )


def _trading_mode_check(capability: ExchangeCapabilityReport) -> ExchangeRuntimeCheck:
    if capability.trading_mode_supported:
        return pass_check(
            stage="trading_mode",
            code="TRADING_MODE_SUPPORTED",
            message="Requested trading mode is supported by the registry profile.",
        )
    return block_check(
        stage="trading_mode",
        code="TRADING_MODE_UNSUPPORTED",
        message="Requested trading mode is not supported by the registry profile.",
        next_action="Choose a supported trading mode or add evidence before expanding support.",
    )


def _credential_check(
    *,
    target: RuntimeVerificationTarget,
    profile: ExchangeCapabilityProfile,
) -> ExchangeRuntimeCheck:
    if target.settings is None:
        required_fields = _required_fields_without_settings(profile)
        if not required_fields:
            return not_required_check(
                stage="credentials",
                code="RUNTIME_CREDENTIALS_NOT_REQUIRED",
                message="Exchange profile does not require credentials.",
            )
        return manual_check(
            stage="credentials",
            code="RUNTIME_CREDENTIALS_NOT_LOADED",
            message="Runtime credentials were not loaded for this report-only check.",
            next_action="Run runtime-check with --config to verify credential readiness.",
        )
    missing = missing_runtime_credential_fields(target.settings)
    if missing:
        return block_check(
            stage="credentials",
            code="RUNTIME_CREDENTIALS_MISSING",
            message="Runtime config is missing exchange credential fields.",
            next_action=f"Add required credential fields: {', '.join(missing)}.",
        )
    return pass_check(
        stage="credentials",
        code="RUNTIME_CREDENTIALS_PRESENT",
        message="Runtime config includes all required exchange credential fields.",
    )


def _read_only_balance_check(
    *,
    profile: ExchangeCapabilityProfile,
    trading_mode: TradingMode,
) -> ExchangeRuntimeCheck:
    evidence = READ_ONLY_BALANCE_EVIDENCE.get(
        f"{profile.exchange_id}:{trading_mode.value}",
    )
    if evidence is not None:
        return pass_check(
            stage="read_only_balance",
            code="READ_ONLY_BALANCE_EVIDENCE_PRESENT",
            message=f"Read-only balance evidence exists at {evidence}.",
        )
    return block_check(
        stage="read_only_balance",
        code="READ_ONLY_BALANCE_EVIDENCE_MISSING",
        message="No read-only balance adapter evidence exists for this exchange mode.",
        next_action="Add a read-only balance adapter test before runtime promotion.",
    )


def _order_lane_check(
    *,
    profile: ExchangeCapabilityProfile,
    trading_mode: TradingMode,
) -> ExchangeRuntimeCheck:
    evidence = ORDER_LANE_EVIDENCE.get(f"{profile.exchange_id}:{trading_mode.value}")
    if evidence is not None:
        return pass_check(
            stage="order_lane",
            code="ORDER_LANE_EVIDENCE_PRESENT",
            message=f"Order-lane evidence exists at {evidence}.",
        )
    match profile.support_level:
        case ExchangeSupportLevel.VERIFIED:
            return block_check(
                stage="order_lane",
                code="ORDER_LANE_EVIDENCE_MISSING",
                message="Verified profile has no order-lane evidence for this mode.",
                next_action="Add mode-specific sandbox/testnet order-lane proof.",
            )
        case ExchangeSupportLevel.CANDIDATE:
            return block_check(
                stage="order_lane",
                code="ORDER_LANE_EVIDENCE_MISSING",
                message="Candidate profile has no runtime order-lane proof yet.",
                next_action="Add sandbox/testnet dry-run order-shape proof before promotion.",
            )
        case ExchangeSupportLevel.GENERIC_UNVERIFIED:
            return block_check(
                stage="order_lane",
                code="ORDER_LANE_PROFILE_UNVERIFIED",
                message="Generic profile cannot run order-lane verification.",
                next_action="Add an explicit exchange profile first.",
            )
        case unreachable:
            assert_never(unreachable)


def _required_fields_without_settings(profile: ExchangeCapabilityProfile) -> tuple[str, ...]:
    if profile.exchange_id == "simulator":
        return ()
    settings = RuntimeSettings()
    exchange_settings = settings.exchange.model_copy(update={"name": profile.exchange_id})
    return required_runtime_credential_fields(
        settings.model_copy(update={"exchange": exchange_settings}),
    )
