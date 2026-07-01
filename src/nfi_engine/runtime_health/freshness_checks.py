from __future__ import annotations

from datetime import datetime, timedelta
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, ValidationError

from nfi_engine.config import RuntimeSettings
from nfi_engine.dashboard import DashboardReadModels
from nfi_engine.execution import ExecutionEventType
from nfi_engine.runtime_health.freshness import latest_dashboard_at
from nfi_engine.runtime_health.models import (
    RuntimeHealthCheck,
    RuntimeHealthCode,
    RuntimeHealthState,
)
from nfi_engine.wallet import WalletBalanceSnapshot, WalletBalanceStatus

CLOCK_SKEW_GRACE_SECONDS = 60


class ReconciliationHealthMetadata(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)

    trading_halted: bool = False


def wallet_freshness_check(
    *,
    settings: RuntimeSettings,
    wallet: WalletBalanceSnapshot,
    generated_at: datetime,
) -> RuntimeHealthCheck:
    if wallet.status is not WalletBalanceStatus.FETCHED:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.WALLET_FRESHNESS,
            state=RuntimeHealthState.DEGRADED,
            message=f"wallet_status={wallet.status.value}",
            next_action="Fetch a wallet snapshot before starting a run.",
        )
    if wallet.captured_at is None:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.WALLET_FRESHNESS,
            state=RuntimeHealthState.BLOCKED,
            message="wallet_captured_at=missing",
            next_action="Refresh wallet sync before starting a run.",
        )
    if wallet.captured_at > generated_at + timedelta(seconds=CLOCK_SKEW_GRACE_SECONDS):
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.WALLET_FRESHNESS,
            state=RuntimeHealthState.BLOCKED,
            message=f"wallet_captured_at={wallet.captured_at.isoformat()}",
            next_action="Fix system clock skew before starting a run.",
        )
    stale_after = timedelta(seconds=settings.circuit_breakers.max_stale_seconds)
    if generated_at - wallet.captured_at > stale_after:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.WALLET_FRESHNESS,
            state=RuntimeHealthState.BLOCKED,
            message=f"wallet_captured_at={wallet.captured_at.isoformat()}",
            next_action="Refresh wallet sync before starting a run.",
        )
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.WALLET_FRESHNESS,
        state=RuntimeHealthState.HEALTHY,
        message=f"wallet_captured_at={wallet.captured_at.isoformat()}",
        next_action="No wallet freshness action required.",
    )


def data_freshness_check(
    *,
    settings: RuntimeSettings,
    read_models: DashboardReadModels,
    generated_at: datetime,
) -> RuntimeHealthCheck:
    latest_at = latest_dashboard_at(read_models)
    if latest_at is None:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.DATA_FRESHNESS,
            state=RuntimeHealthState.DEGRADED,
            message="no dashboard data has been recorded yet",
            next_action="Run paper/testnet once to seed dashboard health data.",
        )
    if latest_at > generated_at + timedelta(seconds=CLOCK_SKEW_GRACE_SECONDS):
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.CLOCK_SKEW,
            state=RuntimeHealthState.BLOCKED,
            message=f"latest_runtime_at={latest_at.isoformat()}",
            next_action="Fix system clock skew before starting a run.",
        )
    stale_after = timedelta(seconds=settings.circuit_breakers.max_stale_seconds)
    if generated_at - latest_at > stale_after:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.DATA_FRESHNESS,
            state=RuntimeHealthState.BLOCKED,
            message=f"latest_runtime_at={latest_at.isoformat()}",
            next_action="Refresh market data before starting a run.",
        )
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.DATA_FRESHNESS,
        state=RuntimeHealthState.HEALTHY,
        message=f"latest_runtime_at={latest_at.isoformat()}",
        next_action="No data freshness action required.",
    )


def reconciliation_age_check(
    *,
    settings: RuntimeSettings,
    read_models: DashboardReadModels,
    generated_at: datetime,
) -> RuntimeHealthCheck:
    event = next(
        (
            candidate
            for candidate in read_models.recent_execution_events
            if candidate.event_type is ExecutionEventType.RECONCILED
        ),
        None,
    )
    if event is None:
        state = (
            RuntimeHealthState.BLOCKED
            if settings.reconciliation.required
            else RuntimeHealthState.DEGRADED
        )
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.RECONCILIATION_AGE,
            state=state,
            message="reconciliation_at=missing",
            next_action="Run reconciliation before starting a supervised pilot.",
        )
    if event.occurred_at > generated_at + timedelta(seconds=CLOCK_SKEW_GRACE_SECONDS):
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.RECONCILIATION_AGE,
            state=RuntimeHealthState.BLOCKED,
            message=f"reconciliation_at={event.occurred_at.isoformat()}",
            next_action="Fix system clock skew before starting a run.",
        )
    if event.raw_status_code == "RECONCILIATION_BLOCKED" or _event_trading_halted(
        event.metadata_json
    ):
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.RECONCILIATION_AGE,
            state=RuntimeHealthState.BLOCKED,
            message=f"reconciliation_status={event.raw_status_code or 'blocked'}",
            next_action="Resolve reconciliation mismatches before starting a run.",
        )
    stale_after = timedelta(seconds=settings.circuit_breakers.max_stale_seconds)
    if generated_at - event.occurred_at > stale_after:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.RECONCILIATION_AGE,
            state=RuntimeHealthState.BLOCKED,
            message=f"reconciliation_at={event.occurred_at.isoformat()}",
            next_action="Run reconciliation again before starting a supervised pilot.",
        )
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.RECONCILIATION_AGE,
        state=RuntimeHealthState.HEALTHY,
        message=f"reconciliation_at={event.occurred_at.isoformat()}",
        next_action="No reconciliation action required.",
    )


def exchange_api_error_check(
    *,
    settings: RuntimeSettings,
    error_count: int,
) -> RuntimeHealthCheck:
    limit = max(0, settings.circuit_breakers.max_api_errors)
    if limit > 0 and error_count >= limit:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.EXCHANGE_API_ERRORS,
            state=RuntimeHealthState.BLOCKED,
            message=f"exchange_api_errors={error_count}",
            next_action="Let exchange API errors cool down before starting a run.",
        )
    if error_count > 0:
        return RuntimeHealthCheck(
            code=RuntimeHealthCode.EXCHANGE_API_ERRORS,
            state=RuntimeHealthState.DEGRADED,
            message=f"exchange_api_errors={error_count}",
            next_action="Monitor exchange API errors before starting a pilot.",
        )
    return RuntimeHealthCheck(
        code=RuntimeHealthCode.EXCHANGE_API_ERRORS,
        state=RuntimeHealthState.HEALTHY,
        message="exchange_api_errors=0",
        next_action="No exchange API error action required.",
    )


def _event_trading_halted(metadata_json: str) -> bool:
    try:
        return ReconciliationHealthMetadata.model_validate_json(metadata_json).trading_halted
    except ValidationError:
        return False
