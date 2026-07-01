from __future__ import annotations

from enum import StrEnum, unique
from typing import ClassVar, Protocol

from pydantic import BaseModel, ConfigDict

from nfi_engine.domain import OrderState
from nfi_engine.exchange.models import ExchangeOrder, ExchangeOrderRequest
from nfi_engine.exchange.testnet_pilot_models import TestnetPilotState


@unique
class TestnetExecutionEventSource(StrEnum):
    INTENT = "intent"
    RISK = "risk"
    ADAPTER = "adapter"
    RECONCILIATION = "reconciliation"


class TestnetExecutionEvent(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    state: TestnetPilotState
    source: TestnetExecutionEventSource


class TestnetExecutionReport(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    exchange: str
    trading_mode: str
    testnet: bool
    execution_ready: bool
    live_money_orders_enabled: bool
    live_exchange_observed: bool
    client_order_id: str
    submitted_order_id: str | None
    adapter_order_state: OrderState | None
    final_state: TestnetPilotState | None
    events: tuple[TestnetExecutionEvent, ...]
    blockers: tuple[str, ...]


class TestnetOrderTestAdapter(Protocol):
    async def test_order(self, request: ExchangeOrderRequest) -> ExchangeOrder: ...
