from __future__ import annotations

from nfi_engine.config.models import RuntimeSettings
from nfi_engine.domain import TradingMode
from nfi_engine.exchange.capabilities import list_exchange_profiles
from nfi_engine.exchange.capability_models import (
    ExchangeCapabilityProfile,
    ExchangeSupportLevel,
)
from nfi_engine.exchange.discovery import build_exchange_capability_report
from nfi_engine.exchange.runtime_verification_checks import (
    RuntimeVerificationTarget,
    build_runtime_checks,
)
from nfi_engine.exchange.runtime_verification_models import (
    ExchangeRuntimeCheck,
    ExchangeRuntimeCheckPayload,
    ExchangeRuntimeCheckStatus,
    ExchangeRuntimeReport,
    ExchangeRuntimeReportCollectionPayload,
    ExchangeRuntimeReportPayload,
)

__all__ = (
    "ExchangeRuntimeCheck",
    "ExchangeRuntimeCheckPayload",
    "ExchangeRuntimeCheckStatus",
    "ExchangeRuntimeReport",
    "ExchangeRuntimeReportCollectionPayload",
    "ExchangeRuntimeReportPayload",
    "build_exchange_runtime_collection_payload",
    "build_exchange_runtime_report",
    "build_exchange_runtime_report_for_profile",
    "build_exchange_runtime_reports",
)


def build_exchange_runtime_report(*, settings: RuntimeSettings) -> ExchangeRuntimeReport:
    return _build_runtime_report(
        target=RuntimeVerificationTarget(
            requested_exchange=settings.exchange.name,
            trading_mode=settings.exchange.trading_mode,
            settings=settings,
        ),
    )


def build_exchange_runtime_report_for_profile(
    *,
    exchange_id: str,
    trading_mode: TradingMode,
) -> ExchangeRuntimeReport:
    return _build_runtime_report(
        target=RuntimeVerificationTarget(
            requested_exchange=exchange_id,
            trading_mode=trading_mode,
            settings=None,
        ),
    )


def build_exchange_runtime_reports() -> tuple[ExchangeRuntimeReport, ...]:
    return tuple(
        build_exchange_runtime_report_for_profile(
            exchange_id=profile.exchange_id,
            trading_mode=trading_mode,
        )
        for profile in list_exchange_profiles()
        if profile.support_level is not ExchangeSupportLevel.GENERIC_UNVERIFIED
        for trading_mode in _supported_modes(profile)
    )


def build_exchange_runtime_collection_payload() -> ExchangeRuntimeReportCollectionPayload:
    return {"reports": [report.to_payload() for report in build_exchange_runtime_reports()]}


def _build_runtime_report(*, target: RuntimeVerificationTarget) -> ExchangeRuntimeReport:
    capability = build_exchange_capability_report(
        exchange_id=target.requested_exchange,
        trading_mode=target.trading_mode,
    )
    return ExchangeRuntimeReport(
        requested_exchange=target.requested_exchange,
        profile=capability.profile,
        trading_mode=target.trading_mode,
        checks=build_runtime_checks(target=target, capability=capability),
    )


def _supported_modes(profile: ExchangeCapabilityProfile) -> tuple[TradingMode, ...]:
    modes: list[TradingMode] = []
    if profile.supports_spot:
        modes.append(TradingMode.SPOT)
    if profile.supports_futures:
        modes.append(TradingMode.FUTURES)
    return tuple(modes)
