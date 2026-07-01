from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique
from typing import ClassVar, Protocol

from pydantic import BaseModel, ConfigDict

from nfi_engine.domain import OrderState, OrderType, PositionSide


@unique
class LiveCanaryOrderBlocker(StrEnum):
    PREVIEW_NOT_READY = "LIVE_CANARY_PREVIEW_NOT_READY"
    PREVIEW_HASH_MISMATCH = "LIVE_CANARY_PREVIEW_HASH_MISMATCH"
    EXECUTION_CONFIRMATION = "LIVE_CANARY_EXECUTION_CONFIRMATION"
    REFERENCE_PRICE = "LIVE_CANARY_REFERENCE_PRICE_REQUIRED"
    LEDGER_DUPLICATE = "LIVE_CANARY_DUPLICATE_CONFIRMATION"
    EXCHANGE_REJECTED = "LIVE_CANARY_EXCHANGE_REJECTED"
    PARTIAL_FILL = "LIVE_CANARY_PARTIAL_FILL_RECONCILIATION_REQUIRED"
    RECONCILIATION = "LIVE_CANARY_RECONCILIATION_FAILED"


@unique
class LiveCanaryOrderEventType(StrEnum):
    INTENT_CREATED = "intent_created"
    PREVIEW_CONFIRMED = "preview_confirmed"
    ENTRY_SUBMITTED = "entry_submitted"
    ENTRY_ACKNOWLEDGED = "entry_acknowledged"
    FILL_RECORDED = "fill_recorded"
    EXIT_SUBMITTED = "exit_submitted"
    EXIT_ACKNOWLEDGED = "exit_acknowledged"
    RECONCILED = "reconciled"
    BLOCKED = "blocked"


class LiveCanaryOrderEvent(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    event_type: LiveCanaryOrderEventType
    message: str
    state: OrderState | None = None
    exchange_order_id: str | None = None
    occurred_at: datetime


class LiveCanaryExchangeOrder(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    exchange_order_id: str
    client_order_id: str
    pair: str
    side: PositionSide
    order_type: OrderType
    state: OrderState
    quantity: Decimal
    filled_quantity: Decimal
    average_price: Decimal | None
    reduce_only: bool
    raw_status_code: str


class LiveCanaryOrderRequest(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    client_order_id: str
    pair: str
    side: PositionSide
    order_type: OrderType
    quantity: Decimal
    leverage: Decimal
    reduce_only: bool


class LiveCanaryExecutionClient(Protocol):
    async def submit_order(self, request: LiveCanaryOrderRequest) -> LiveCanaryExchangeOrder: ...

    async def fetch_order(self, request: LiveCanaryOrderRequest) -> LiveCanaryExchangeOrder: ...


class LiveCanaryOrderReport(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    ready: bool
    executed: bool
    live_money_orders_enabled: bool
    duplicate_rejected: bool
    exchange: str
    production: bool
    preview_hash: str
    client_order_id: str | None
    pair: str | None
    canary_notional_usdt: Decimal | None
    reference_price_usdt: Decimal | None
    quantity: Decimal | None
    entry_order_id: str | None
    exit_order_id: str | None
    reconciliation_status: str
    events: tuple[LiveCanaryOrderEvent, ...]
    blockers: tuple[str, ...]


class LiveCanaryClientError(Exception):
    code: str
    message: str

    def __init__(self, code: str, message: str) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
