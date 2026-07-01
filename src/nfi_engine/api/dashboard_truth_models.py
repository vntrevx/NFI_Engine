from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from nfi_engine.dashboard.models import (
    DashboardExecutionEvent,
    DashboardExecutionFill,
    DashboardExecutionIntent,
    DashboardExecutionOrder,
)
from nfi_engine.dashboard.truth_models import (
    DashboardAccountTruth,
    DashboardBalanceTruth,
    DashboardExposureTruth,
    DashboardPnlTruth,
    DashboardReconciliationTruth,
)


class StrictDashboardTruthApiModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


class DashboardBalanceTruthResponse(StrictDashboardTruthApiModel):
    equity: str
    available: str
    synced_at: str | None
    stale: bool

    @classmethod
    def from_truth(cls, truth: DashboardBalanceTruth) -> DashboardBalanceTruthResponse:
        return cls(
            equity=_decimal_json(truth.equity),
            available=_decimal_json(truth.available),
            synced_at=None if truth.synced_at is None else _datetime_json(truth.synced_at),
            stale=truth.stale,
        )


class DashboardPnlTruthResponse(StrictDashboardTruthApiModel):
    open_profit: str | None
    closed_profit: str
    wins: int
    losses: int
    breakeven: int
    stale_data: bool
    stale_pairs: tuple[str, ...]
    confident_open_values: bool

    @classmethod
    def from_truth(cls, truth: DashboardPnlTruth) -> DashboardPnlTruthResponse:
        return cls(
            open_profit=None if truth.open_profit is None else _decimal_json(truth.open_profit),
            closed_profit=_decimal_json(truth.closed_profit),
            wins=truth.wins,
            losses=truth.losses,
            breakeven=truth.breakeven,
            stale_data=truth.stale_data,
            stale_pairs=truth.stale_pairs,
            confident_open_values=truth.confident_open_values,
        )


class DashboardExposureTruthResponse(StrictDashboardTruthApiModel):
    open_notional: str | None
    account_exposure: str | None
    exposure_pct: str | None
    realized_quote_fees: str
    partial_fills: int

    @classmethod
    def from_truth(cls, truth: DashboardExposureTruth) -> DashboardExposureTruthResponse:
        return cls(
            open_notional=None
            if truth.open_notional is None
            else _decimal_json(truth.open_notional),
            account_exposure=(
                None if truth.account_exposure is None else _decimal_json(truth.account_exposure)
            ),
            exposure_pct=None if truth.exposure_pct is None else _decimal_json(truth.exposure_pct),
            realized_quote_fees=_decimal_json(truth.realized_quote_fees),
            partial_fills=truth.partial_fills,
        )


class DashboardReconciliationTruthResponse(StrictDashboardTruthApiModel):
    status: str
    trading_halted: bool
    mismatch_count: int
    issue_codes: tuple[str, ...]
    checked_at: str | None

    @classmethod
    def from_truth(
        cls,
        truth: DashboardReconciliationTruth,
    ) -> DashboardReconciliationTruthResponse:
        return cls(
            status=truth.status,
            trading_halted=truth.trading_halted,
            mismatch_count=truth.mismatch_count,
            issue_codes=truth.issue_codes,
            checked_at=None if truth.checked_at is None else _datetime_json(truth.checked_at),
        )


class DashboardAccountTruthResponse(StrictDashboardTruthApiModel):
    balance: DashboardBalanceTruthResponse
    pnl: DashboardPnlTruthResponse
    exposure: DashboardExposureTruthResponse
    reconciliation: DashboardReconciliationTruthResponse

    @classmethod
    def from_truth(cls, truth: DashboardAccountTruth) -> DashboardAccountTruthResponse:
        return cls(
            balance=DashboardBalanceTruthResponse.from_truth(truth.balance),
            pnl=DashboardPnlTruthResponse.from_truth(truth.pnl),
            exposure=DashboardExposureTruthResponse.from_truth(truth.exposure),
            reconciliation=DashboardReconciliationTruthResponse.from_truth(truth.reconciliation),
        )


class DashboardExecutionIntentResponse(StrictDashboardTruthApiModel):
    intent_id: str
    pair: str
    side: str
    state: str
    requested_quantity: str
    requested_price: str | None
    updated_at: str

    @classmethod
    def from_intent(cls, intent: DashboardExecutionIntent) -> DashboardExecutionIntentResponse:
        return cls(
            intent_id=intent.intent_id,
            pair=intent.pair,
            side=intent.side.value,
            state=intent.state.value,
            requested_quantity=_decimal_json(intent.requested_quantity),
            requested_price=(
                None if intent.requested_price is None else _decimal_json(intent.requested_price)
            ),
            updated_at=_datetime_json(intent.updated_at),
        )


class DashboardExecutionOrderResponse(StrictDashboardTruthApiModel):
    execution_order_id: str
    intent_id: str
    pair: str
    side: str
    state: str
    requested_quantity: str
    requested_price: str | None
    filled_quantity: str
    average_fill_price: str | None
    updated_at: str

    @classmethod
    def from_order(cls, order: DashboardExecutionOrder) -> DashboardExecutionOrderResponse:
        return cls(
            execution_order_id=order.execution_order_id,
            intent_id=order.intent_id,
            pair=order.pair,
            side=order.side.value,
            state=order.state.value,
            requested_quantity=_decimal_json(order.requested_quantity),
            requested_price=(
                None if order.requested_price is None else _decimal_json(order.requested_price)
            ),
            filled_quantity=_decimal_json(order.filled_quantity),
            average_fill_price=(
                None
                if order.average_fill_price is None
                else _decimal_json(order.average_fill_price)
            ),
            updated_at=_datetime_json(order.updated_at),
        )


class DashboardExecutionFillResponse(StrictDashboardTruthApiModel):
    execution_fill_id: str
    intent_id: str
    execution_order_id: str
    pair: str
    side: str
    quantity: str
    price: str
    fee_asset: str | None
    fee_amount: str | None
    filled_at: str

    @classmethod
    def from_fill(cls, fill: DashboardExecutionFill) -> DashboardExecutionFillResponse:
        return cls(
            execution_fill_id=fill.execution_fill_id,
            intent_id=fill.intent_id,
            execution_order_id=fill.execution_order_id,
            pair=fill.pair,
            side=fill.side.value,
            quantity=_decimal_json(fill.quantity),
            price=_decimal_json(fill.price),
            fee_asset=fill.fee_asset,
            fee_amount=None if fill.fee_amount is None else _decimal_json(fill.fee_amount),
            filled_at=_datetime_json(fill.filled_at),
        )


class DashboardExecutionEventResponse(StrictDashboardTruthApiModel):
    event_id: int | None
    intent_id: str
    event_type: str
    state: str
    message: str
    raw_status_code: str | None
    occurred_at: str

    @classmethod
    def from_event(cls, event: DashboardExecutionEvent) -> DashboardExecutionEventResponse:
        return cls(
            event_id=event.event_id,
            intent_id=event.intent_id,
            event_type=event.event_type.value,
            state=event.state.value,
            message=event.message,
            raw_status_code=event.raw_status_code,
            occurred_at=_datetime_json(event.occurred_at),
        )


def _datetime_json(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decimal_json(value: Decimal) -> str:
    return str(value)
