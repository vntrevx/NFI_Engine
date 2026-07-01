from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal

from sqlalchemy.exc import IntegrityError

from nfi_engine.domain import OrderType, PositionSide
from nfi_engine.exchange.live_canary_order_models import (
    LiveCanaryExchangeOrder,
    LiveCanaryOrderEvent,
    LiveCanaryOrderEventType,
)
from nfi_engine.execution import ExecutionEventType, ExecutionState
from nfi_engine.persistence.records import (
    ExecutionEventRecord,
    ExecutionFillRecord,
    ExecutionIntentRecord,
    ExecutionOrderRecord,
)
from nfi_engine.persistence.repositories import (
    ExecutionEventRepository,
    ExecutionFillRepository,
    ExecutionIntentRepository,
    ExecutionOrderRepository,
)
from nfi_engine.persistence.session import PersistenceDatabase


async def reserve_live_canary_intent(  # noqa: PLR0913
    database: PersistenceDatabase,
    *,
    intent_id: str,
    idempotency_key: str,
    client_order_id: str,
    pair: str,
    order_type: OrderType,
    quantity: Decimal,
    metadata_json: str,
    now: datetime,
) -> bool:
    async with database.session() as session:
        await ExecutionIntentRepository(session).create(
            ExecutionIntentRecord(
                intent_id=intent_id,
                idempotency_key=idempotency_key,
                client_order_id=client_order_id,
                pair=pair,
                side=PositionSide.LONG,
                order_type=order_type,
                requested_quantity=quantity,
                requested_price=None,
                state=ExecutionState.INTENT_CREATED,
                raw_status_code=None,
                metadata_json=metadata_json,
                created_at=now,
                updated_at=now,
                exchange_created_at=None,
                exchange_updated_at=None,
            ),
        )
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            return False
    return True


async def write_live_canary_event(
    database: PersistenceDatabase,
    *,
    intent_id: str,
    event: LiveCanaryOrderEvent,
) -> None:
    async with database.session() as session:
        await ExecutionEventRepository(session).append(
            ExecutionEventRecord(
                event_id=None,
                intent_id=intent_id,
                event_type=_execution_event_type(event.event_type),
                state=_execution_state(event.event_type, event.state),
                message=event.message,
                raw_status_code=event.state.value if event.state is not None else None,
                metadata_json=json.dumps(
                    {"exchange_order_id": event.exchange_order_id},
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                occurred_at=event.occurred_at,
            ),
        )
        await session.commit()


async def write_live_canary_order(
    database: PersistenceDatabase,
    *,
    intent_id: str,
    execution_order_id: str,
    order: LiveCanaryExchangeOrder,
    now: datetime,
) -> None:
    async with database.session() as session:
        await ExecutionOrderRepository(session).create(
            ExecutionOrderRecord(
                execution_order_id=execution_order_id,
                intent_id=intent_id,
                client_order_id=order.client_order_id,
                exchange_order_id=order.exchange_order_id,
                pair=order.pair,
                side=order.side,
                order_type=order.order_type,
                requested_quantity=order.quantity,
                requested_price=None,
                filled_quantity=order.filled_quantity,
                average_fill_price=order.average_price,
                state=_state_from_order(order.state),
                raw_status_code=order.raw_status_code,
                metadata_json=json.dumps(
                    {"reduce_only": order.reduce_only},
                    separators=(",", ":"),
                    sort_keys=True,
                ),
                created_at=now,
                updated_at=now,
                exchange_created_at=now,
                exchange_updated_at=now,
            ),
        )
        if order.filled_quantity > 0 and order.average_price is not None:
            await ExecutionFillRepository(session).create(
                ExecutionFillRecord(
                    execution_fill_id=f"{execution_order_id}-fill",
                    intent_id=intent_id,
                    execution_order_id=execution_order_id,
                    exchange_order_id=order.exchange_order_id,
                    pair=order.pair,
                    side=order.side,
                    quantity=order.filled_quantity,
                    price=order.average_price,
                    fee_asset=None,
                    fee_amount=None,
                    metadata_json='{"source":"live-canary"}',
                    filled_at=now,
                ),
            )
        await session.commit()


def _execution_event_type(event_type: LiveCanaryOrderEventType) -> ExecutionEventType:
    mapping = {
        LiveCanaryOrderEventType.INTENT_CREATED: ExecutionEventType.INTENT_CREATED,
        LiveCanaryOrderEventType.PREVIEW_CONFIRMED: ExecutionEventType.RISK_CHECKED,
        LiveCanaryOrderEventType.ENTRY_SUBMITTED: ExecutionEventType.ORDER_SUBMITTED,
        LiveCanaryOrderEventType.ENTRY_ACKNOWLEDGED: ExecutionEventType.ORDER_ACKNOWLEDGED,
        LiveCanaryOrderEventType.FILL_RECORDED: ExecutionEventType.FILL_RECORDED,
        LiveCanaryOrderEventType.EXIT_SUBMITTED: ExecutionEventType.CANCEL_REQUESTED,
        LiveCanaryOrderEventType.EXIT_ACKNOWLEDGED: ExecutionEventType.ORDER_CANCELED,
        LiveCanaryOrderEventType.RECONCILED: ExecutionEventType.RECONCILED,
        LiveCanaryOrderEventType.BLOCKED: ExecutionEventType.KILL_SWITCH_TRIGGERED,
    }
    return mapping[event_type]


def _execution_state(
    event_type: LiveCanaryOrderEventType,
    order_state: object | None,
) -> ExecutionState:
    if order_state is not None:
        return _state_from_order(order_state)
    if event_type is LiveCanaryOrderEventType.PREVIEW_CONFIRMED:
        return ExecutionState.RISK_CHECKED
    if event_type is LiveCanaryOrderEventType.BLOCKED:
        return ExecutionState.REJECTED
    return ExecutionState.INTENT_CREATED


def _state_from_order(order_state: object) -> ExecutionState:
    value = getattr(order_state, "value", "")
    if value == "open":
        return ExecutionState.ACKNOWLEDGED
    if value == "partially_filled":
        return ExecutionState.PARTIALLY_FILLED
    if value == "filled":
        return ExecutionState.FILLED
    if value == "canceled":
        return ExecutionState.CANCELED
    if value == "rejected":
        return ExecutionState.REJECTED
    return ExecutionState.SUBMITTED
