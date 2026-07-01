from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from nfi_engine.config import RuntimeSettings
from nfi_engine.dashboard.execution_aggregate import summarize_dashboard_execution_aggregate
from nfi_engine.dashboard.models import (
    DashboardExecutionEvent,
    DashboardReadModels,
)
from nfi_engine.dashboard.truth_models import (
    DashboardAccountTruth,
    DashboardBalanceTruth,
    DashboardExposureTruth,
    DashboardPnlTruth,
    DashboardReconciliationTruth,
)
from nfi_engine.events import redact_text
from nfi_engine.execution import ExecutionEventType

ACCOUNT_TRUTH_STALE_AFTER: Final = timedelta(minutes=5)
PERCENT_MULTIPLIER: Final = Decimal(100)
RECONCILIATION_BLOCKED: Final = "blocked"
RECONCILIATION_CLEAR: Final = "clear"
RECONCILIATION_MISSING: Final = "missing"
RECONCILIATION_METADATA_INVALID: Final = "RECONCILIATION_METADATA_INVALID"
RECONCILIATION_UNKNOWN: Final = "unknown"
ZERO: Final = Decimal(0)


class ReconciliationEventMetadata(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="ignore", frozen=True)

    trading_halted: bool = False
    mismatch_count: int = 0
    issue_codes: tuple[str, ...] = ()


def build_dashboard_account_truth(
    read_models: DashboardReadModels,
    *,
    now: datetime,
    stale_after: timedelta = ACCOUNT_TRUTH_STALE_AFTER,
) -> DashboardAccountTruth:
    aggregate = summarize_dashboard_execution_aggregate(
        read_models,
        now=now,
        stale_after=stale_after,
    )
    balance = _balance_truth(read_models, now=now, stale_after=stale_after)
    return DashboardAccountTruth(
        balance=balance,
        pnl=DashboardPnlTruth(
            open_profit=aggregate.open_profit,
            closed_profit=aggregate.closed_profit,
            wins=aggregate.wins,
            losses=aggregate.losses,
            breakeven=aggregate.breakeven,
            stale_data=aggregate.stale_data,
            stale_pairs=aggregate.stale_pairs,
            confident_open_values=aggregate.confident_open_values,
        ),
        exposure=DashboardExposureTruth(
            open_notional=aggregate.open_notional,
            account_exposure=aggregate.account_exposure,
            exposure_pct=_exposure_pct(
                account_exposure=aggregate.account_exposure,
                account_equity=balance.equity,
            ),
            realized_quote_fees=aggregate.realized_quote_fees,
            partial_fills=aggregate.partial_fills,
        ),
        reconciliation=_reconciliation_truth(read_models.recent_execution_events),
    )


def redact_dashboard_execution_events(
    events: tuple[DashboardExecutionEvent, ...],
    *,
    settings: RuntimeSettings,
) -> tuple[DashboardExecutionEvent, ...]:
    secrets = _secret_values(settings)
    if secrets == ():
        return events
    return tuple(
        replace(
            event,
            message=redact_text(event.message, secrets=secrets),
            raw_status_code=(
                None
                if event.raw_status_code is None
                else redact_text(event.raw_status_code, secrets=secrets)
            ),
        )
        for event in events
    )


def _balance_truth(
    read_models: DashboardReadModels,
    *,
    now: datetime,
    stale_after: timedelta,
) -> DashboardBalanceTruth:
    if read_models.equity_points == ():
        return DashboardBalanceTruth(
            equity=ZERO,
            available=ZERO,
            synced_at=None,
            stale=True,
        )
    point = read_models.equity_points[-1]
    return DashboardBalanceTruth(
        equity=point.equity,
        available=point.available,
        synced_at=point.at,
        stale=now - point.at > stale_after,
    )


def _exposure_pct(
    *,
    account_exposure: Decimal | None,
    account_equity: Decimal,
) -> Decimal | None:
    if account_exposure is None:
        return None
    if account_equity <= ZERO:
        return ZERO
    return (account_exposure / account_equity) * PERCENT_MULTIPLIER


def _reconciliation_truth(
    events: tuple[DashboardExecutionEvent, ...],
) -> DashboardReconciliationTruth:
    event = next(
        (
            candidate
            for candidate in events
            if candidate.event_type is ExecutionEventType.RECONCILED
        ),
        None,
    )
    if event is None:
        return DashboardReconciliationTruth(
            status=RECONCILIATION_MISSING,
            trading_halted=True,
            mismatch_count=0,
            issue_codes=(),
            checked_at=None,
        )
    metadata = _metadata(event.metadata_json)
    if metadata is None:
        return DashboardReconciliationTruth(
            status=RECONCILIATION_BLOCKED,
            trading_halted=True,
            mismatch_count=0,
            issue_codes=(RECONCILIATION_METADATA_INVALID,),
            checked_at=event.occurred_at,
        )
    trading_halted = metadata.trading_halted
    mismatch_count = max(0, metadata.mismatch_count)
    issue_codes = metadata.issue_codes
    if event.raw_status_code == "RECONCILIATION_CLEAR" and not trading_halted:
        status = RECONCILIATION_CLEAR
    elif event.raw_status_code == "RECONCILIATION_BLOCKED" or trading_halted:
        status = RECONCILIATION_BLOCKED
        trading_halted = True
    else:
        status = RECONCILIATION_UNKNOWN
    return DashboardReconciliationTruth(
        status=status,
        trading_halted=trading_halted,
        mismatch_count=mismatch_count,
        issue_codes=issue_codes,
        checked_at=event.occurred_at,
    )


def _metadata(value: str) -> ReconciliationEventMetadata | None:
    try:
        return ReconciliationEventMetadata.model_validate_json(value)
    except ValidationError:
        return None


def _secret_values(settings: RuntimeSettings) -> tuple[str, ...]:
    values = (
        settings.exchange.api_key,
        settings.exchange.api_secret,
        settings.exchange.passphrase,
        settings.exchange.memo,
        settings.exchange.operator_id,
        settings.exchange.account_address,
        settings.exchange.api_wallet_signer,
        settings.api.auth_token,
        settings.api.operator_password,
        settings.notifications.webhook_url,
        settings.notifications.discord_webhook_url,
        settings.notifications.telegram_bot_token,
    )
    return tuple(value for value in values if value is not None and value != "")
