from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import OrderState, PositionSide
from nfi_engine.exchange.live_canary_ledger import write_live_canary_order
from nfi_engine.exchange.live_canary_order_events import (
    append_live_canary_event,
    append_live_canary_order_event,
)
from nfi_engine.exchange.live_canary_order_models import (
    LiveCanaryExchangeOrder,
    LiveCanaryExecutionClient,
    LiveCanaryOrderBlocker,
    LiveCanaryOrderEvent,
    LiveCanaryOrderEventType,
    LiveCanaryOrderReport,
    LiveCanaryOrderRequest,
)
from nfi_engine.exchange.live_canary_order_reports import execution_report
from nfi_engine.persistence.session import PersistenceDatabase


async def submit_live_canary_exit(  # noqa: PLR0913
    settings: RuntimeSettings,
    database: PersistenceDatabase,
    order_client: LiveCanaryExecutionClient,
    expected_hash: str,
    client_order_id: str,
    intent_id: str,
    reference_price_usdt: Decimal,
    quantity: Decimal,
    entry_request: LiveCanaryOrderRequest,
    fetched_entry: LiveCanaryExchangeOrder,
    events: list[LiveCanaryOrderEvent],
    observed_at: datetime,
    exit_blockers: tuple[str, ...] = (),
) -> LiveCanaryOrderReport:
    exit_request = entry_request.model_copy(
        update={
            "client_order_id": f"{client_order_id}-exit",
            "side": PositionSide.SHORT,
            "reduce_only": True,
            "quantity": fetched_entry.filled_quantity,
        },
    )
    exit_order = await order_client.submit_order(exit_request)
    await write_live_canary_order(
        database,
        intent_id=intent_id,
        execution_order_id=f"{intent_id}-exit",
        order=exit_order,
        now=observed_at,
    )
    await append_live_canary_order_event(
        database,
        intent_id,
        events,
        LiveCanaryOrderEventType.EXIT_SUBMITTED,
        "reduce-only exit submitted",
        exit_order,
        observed_at,
    )
    if exit_order.state is not OrderState.FILLED:
        blocker = (*exit_blockers, LiveCanaryOrderBlocker.RECONCILIATION.value)
        return execution_report(
            settings,
            expected_hash,
            client_order_id,
            reference_price_usdt,
            quantity,
            events,
            blocker,
            entry_order_id=fetched_entry.exchange_order_id,
            exit_order_id=exit_order.exchange_order_id,
        )
    await append_live_canary_order_event(
        database,
        intent_id,
        events,
        LiveCanaryOrderEventType.EXIT_ACKNOWLEDGED,
        "reduce-only exit filled",
        exit_order,
        observed_at,
    )
    if exit_blockers == ():
        await append_live_canary_event(
            database,
            intent_id,
            events,
            LiveCanaryOrderEventType.RECONCILED,
            "entry and exit reconciled",
            observed_at,
        )
    else:
        await append_live_canary_event(
            database,
            intent_id,
            events,
            LiveCanaryOrderEventType.BLOCKED,
            "partial fill exposure exited; manual reconciliation required",
            observed_at,
        )
    return execution_report(
        settings,
        expected_hash,
        client_order_id,
        reference_price_usdt,
        quantity,
        events,
        exit_blockers,
        entry_order_id=fetched_entry.exchange_order_id,
        exit_order_id=exit_order.exchange_order_id,
    )
