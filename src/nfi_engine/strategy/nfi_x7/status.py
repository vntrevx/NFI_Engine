from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique

from nfi_engine.config import RuntimeSettings
from nfi_engine.preflight.models import PreflightReport, PreflightStatus
from nfi_engine.strategy.nfi_x7.coverage import (
    X7CoverageReport,
    X7CoverageStatus,
    build_x7_coverage_report,
    worktree_evidence_available,
)
from nfi_engine.strategy.nfi_x7.metadata import X7_METADATA

X7_NATIVE_MODULE = "nfi_engine.strategy.nfi_x7:X7NativeStrategy"
X7_NATIVE_NAME = "X7NativeStrategy"
NO_RUNTIME_SIGNAL_REASON = "no_runtime_signal_observed"
X7_DISABLED_REASON = "x7_strategy_disabled"


@unique
class X7SemanticCoverageState(StrEnum):
    DISABLED = "disabled"
    VERIFIED = "verified"
    UNDER_DEVELOPMENT = "under_development"
    BLOCKED = "blocked"


@unique
class X7LiveReadiness(StrEnum):
    DISABLED = "disabled"
    GATED = "gated"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class X7SemanticStatus:
    enabled: bool
    coverage_state: X7SemanticCoverageState
    observed_upstream_version: str
    provenance_evidence_path: str
    covered_modules: tuple[str, ...]
    pending_modules: tuple[str, ...]
    latest_signal_reason: str
    warmup_state: str
    missing_data_state: str
    live_readiness: X7LiveReadiness
    blocked_reason: str | None
    next_action: str


def build_x7_semantic_status(
    *,
    settings: RuntimeSettings,
    readiness: PreflightReport | None,
    coverage_report: X7CoverageReport | None = None,
    dashboard_data_observed: bool = False,
    latest_signal_reason: str | None = None,
) -> X7SemanticStatus:
    if not is_x7_native_settings(settings):
        return _disabled_status()
    report = (
        coverage_report
        if coverage_report is not None
        else build_x7_coverage_report(
            require_evidence_artifacts=worktree_evidence_available(),
        )
    )
    preflight_blocker = _preflight_blocker(readiness)
    coverage_blocker = _coverage_blocker(report)
    blocked_reason = preflight_blocker or coverage_blocker
    coverage_pending = len(report.pending_modules) > 0
    return X7SemanticStatus(
        enabled=True,
        coverage_state=_coverage_state(report),
        observed_upstream_version=X7_METADATA.observed_upstream_version,
        provenance_evidence_path=X7_METADATA.provenance_evidence_path,
        covered_modules=report.covered_modules,
        pending_modules=report.pending_modules,
        latest_signal_reason=latest_signal_reason or NO_RUNTIME_SIGNAL_REASON,
        warmup_state=_warmup_state(dashboard_data_observed),
        missing_data_state=_missing_data_state(dashboard_data_observed),
        live_readiness=_live_readiness(settings=settings, preflight_blocker=preflight_blocker),
        blocked_reason=blocked_reason,
        next_action=_next_action(
            preflight_blocker=preflight_blocker,
            coverage_blocker=coverage_blocker,
            coverage_pending=coverage_pending,
            dashboard_data_observed=dashboard_data_observed,
        ),
    )


def is_x7_native_settings(settings: RuntimeSettings) -> bool:
    return settings.strategy.module == X7_NATIVE_MODULE or settings.strategy.name == X7_NATIVE_NAME


def _disabled_status() -> X7SemanticStatus:
    return X7SemanticStatus(
        enabled=False,
        coverage_state=X7SemanticCoverageState.DISABLED,
        observed_upstream_version="",
        provenance_evidence_path="",
        covered_modules=(),
        pending_modules=(),
        latest_signal_reason=X7_DISABLED_REASON,
        warmup_state="disabled",
        missing_data_state="disabled",
        live_readiness=X7LiveReadiness.DISABLED,
        blocked_reason=None,
        next_action="Select X7NativeStrategy to inspect native X7 semantic status.",
    )


def _coverage_state(report: X7CoverageReport) -> X7SemanticCoverageState:
    if any(module.status is X7CoverageStatus.BLOCKED for module in report.modules):
        return X7SemanticCoverageState.BLOCKED
    if report.is_full_semantic_coverage:
        return X7SemanticCoverageState.VERIFIED
    return X7SemanticCoverageState.UNDER_DEVELOPMENT


def _coverage_blocker(report: X7CoverageReport) -> str | None:
    for module in report.modules:
        if module.status is X7CoverageStatus.BLOCKED:
            reason = module.blocker or "Semantic module is blocked."
            return f"{module.name}: {reason}"
    return None


def _preflight_blocker(readiness: PreflightReport | None) -> str | None:
    if readiness is None:
        return None
    for check in readiness.checks:
        if check.status is PreflightStatus.BLOCK:
            return f"{check.code.value}: {check.message}"
    return None


def _warmup_state(dashboard_data_observed: bool) -> str:
    if dashboard_data_observed:
        return "observed"
    return "not_observed"


def _missing_data_state(dashboard_data_observed: bool) -> str:
    if dashboard_data_observed:
        return "observed"
    return "no_dashboard_data"


def _live_readiness(
    *,
    settings: RuntimeSettings,
    preflight_blocker: str | None,
) -> X7LiveReadiness:
    if settings.engine.live_trading or preflight_blocker is not None:
        return X7LiveReadiness.BLOCKED
    return X7LiveReadiness.GATED


def _next_action(
    *,
    preflight_blocker: str | None,
    coverage_blocker: str | None,
    coverage_pending: bool,
    dashboard_data_observed: bool,
) -> str:
    if preflight_blocker is not None:
        return "Resolve blocked preflight checks before starting an X7 paper/testnet run."
    if coverage_blocker is not None:
        return "Keep X7 in paper/testnet and restore the missing semantic evidence artifact."
    if coverage_pending:
        return "Keep X7 in paper/testnet and finish the remaining semantic evidence items."
    if not dashboard_data_observed:
        return "Run paper/testnet once to observe the latest X7 signal and warmup state."
    return "Review gated X7 paper/testnet status before any runtime action."
