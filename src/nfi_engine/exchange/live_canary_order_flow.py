from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import OrderState
from nfi_engine.exchange.live_canary_ledger import write_live_canary_order
from nfi_engine.exchange.live_canary_order_events import (
    append_live_canary_event,
    append_live_canary_order_event,
    safe_exchange_message,
)
from nfi_engine.exchange.live_canary_order_exit import submit_live_canary_exit
from nfi_engine.exchange.live_canary_order_models import (
    LiveCanaryClientError,
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


async def execute_live_canary_flow(  # noqa: PLR0913
    *,
    settings: RuntimeSettings,
    database: PersistenceDatabase,
    order_client: LiveCanaryExecutionClient,
    expected_hash: str,
    client_order_id: str,
    intent_id: str,
    reference_price_usdt: Decimal,
    quantity: Decimal,
    entry_request: LiveCanaryOrderRequest,
    observed_at: datetime,
) -> LiveCanaryOrderReport:
    events: list[LiveCanaryOrderEvent] = []
    await append_live_canary_event(
        database,
        intent_id,
        events,
        LiveCanaryOrderEventType.INTENT_CREATED,
        "intent reserved",
        observed_at,
    )
    await append_live_canary_event(
        database,
        intent_id,
        events,
        LiveCanaryOrderEventType.PREVIEW_CONFIRMED,
        "preview hash confirmed",
        observed_at,
    )
    try:
        entry = await order_client.submit_order(entry_request)
        await append_live_canary_order_event(
            database,
            intent_id,
            events,
            LiveCanaryOrderEventType.ENTRY_SUBMITTED,
            "entry order submitted",
            entry,
            observed_at,
        )
        fetched_entry = await order_client.fetch_order(entry_request)
    except LiveCanaryClientError as exc:
        blocker = (exc.code,)
        await append_live_canary_event(
            database,
            intent_id,
            events,
            LiveCanaryOrderEventType.BLOCKED,
            safe_exchange_message(settings, exc.message),
            observed_at,
        )
        return execution_report(
            settings,
            expected_hash,
            client_order_id,
            reference_price_usdt,
            quantity,
            events,
            blocker,
        )
    return await _complete_entry(
        settings=settings,
        database=database,
        order_client=order_client,
        expected_hash=expected_hash,
        client_order_id=client_order_id,
        intent_id=intent_id,
        reference_price_usdt=reference_price_usdt,
        quantity=quantity,
        entry_request=entry_request,
        fetched_entry=fetched_entry,
        events=events,
        observed_at=observed_at,
    )


async def _complete_entry(  # noqa: PLR0913
    *,
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
) -> LiveCanaryOrderReport:
    await write_live_canary_order(
        database,
        intent_id=intent_id,
        execution_order_id=f"{intent_id}-entry",
        order=fetched_entry,
        now=observed_at,
    )
    if fetched_entry.state is OrderState.PARTIALLY_FILLED:
        return await _partial_fill_report(
            settings,
            database,
            order_client,
            expected_hash,
            client_order_id,
            intent_id,
            reference_price_usdt,
            quantity,
            entry_request,
            fetched_entry,
            events,
            observed_at,
        )
    if fetched_entry.state is not OrderState.FILLED:
        blocker = (LiveCanaryOrderBlocker.RECONCILIATION.value,)
        await append_live_canary_order_event(
            database,
            intent_id,
            events,
            LiveCanaryOrderEventType.BLOCKED,
            "entry order did not reconcile filled",
            fetched_entry,
            observed_at,
        )
        return execution_report(
            settings,
            expected_hash,
            client_order_id,
            reference_price_usdt,
            quantity,
            events,
            blocker,
            entry_order_id=fetched_entry.exchange_order_id,
        )
    await append_live_canary_order_event(
        database,
        intent_id,
        events,
        LiveCanaryOrderEventType.FILL_RECORDED,
        "entry fill recorded",
        fetched_entry,
        observed_at,
    )
    return await submit_live_canary_exit(
        settings,
        database,
        order_client,
        expected_hash,
        client_order_id,
        intent_id,
        reference_price_usdt,
        quantity,
        entry_request,
        fetched_entry,
        events,
        observed_at,
    )


async def _partial_fill_report(  # noqa: PLR0913
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
) -> LiveCanaryOrderReport:
    blocker = (LiveCanaryOrderBlocker.PARTIAL_FILL.value,)
    await append_live_canary_order_event(
        database,
        intent_id,
        events,
        LiveCanaryOrderEventType.FILL_RECORDED,
        "partial fill recorded; reducing filled exposure",
        fetched_entry,
        observed_at,
    )
    if fetched_entry.filled_quantity <= Decimal(0):
        await append_live_canary_event(
            database,
            intent_id,
            events,
            LiveCanaryOrderEventType.BLOCKED,
            "partial fill has no filled quantity to reduce",
            observed_at,
        )
        return execution_report(
            settings,
            expected_hash,
            client_order_id,
            reference_price_usdt,
            quantity,
            events,
            blocker,
            entry_order_id=fetched_entry.exchange_order_id,
        )
    return await submit_live_canary_exit(
        settings,
        database,
        order_client,
        expected_hash,
        client_order_id,
        intent_id,
        reference_price_usdt,
        quantity,
        entry_request,
        fetched_entry,
        events,
        observed_at,
        exit_blockers=blocker,
    )
