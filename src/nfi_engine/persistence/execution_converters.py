from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from nfi_engine.domain import OrderType, PositionSide
from nfi_engine.execution import ExecutionEventType, ExecutionState
from nfi_engine.persistence.converters import (
    datetime_from_storage,
    datetime_to_storage,
    decimal_from_storage,
    decimal_to_storage,
)
from nfi_engine.persistence.execution_metadata import redacted_execution_metadata_json
from nfi_engine.persistence.models import (
    ExecutionEventRow,
    ExecutionFillRow,
    ExecutionIntentRow,
    ExecutionOrderRow,
)
from nfi_engine.persistence.records import (
    ExecutionEventRecord,
    ExecutionFillRecord,
    ExecutionIntentRecord,
    ExecutionOrderRecord,
)


def execution_intent_row(record: ExecutionIntentRecord) -> ExecutionIntentRow:
    row = ExecutionIntentRow()
    row.intent_id = record.intent_id
    row.idempotency_key = record.idempotency_key
    row.client_order_id = record.client_order_id
    row.pair = record.pair
    row.side = record.side.value
    row.order_type = record.order_type.value
    row.requested_quantity = decimal_to_storage(record.requested_quantity)
    row.requested_price = _optional_decimal_to_storage(record.requested_price)
    row.state = record.state.value
    row.raw_status_code = record.raw_status_code
    row.metadata_json = redacted_execution_metadata_json(record.metadata_json)
    row.created_at = datetime_to_storage(record.created_at)
    row.updated_at = datetime_to_storage(record.updated_at)
    row.exchange_created_at = _optional_datetime_to_storage(record.exchange_created_at)
    row.exchange_updated_at = _optional_datetime_to_storage(record.exchange_updated_at)
    return row


def execution_intent_record_from_row(row: ExecutionIntentRow) -> ExecutionIntentRecord:
    return ExecutionIntentRecord(
        intent_id=row.intent_id,
        idempotency_key=row.idempotency_key,
        client_order_id=row.client_order_id,
        pair=row.pair,
        side=PositionSide(row.side),
        order_type=OrderType(row.order_type),
        requested_quantity=decimal_from_storage(row.requested_quantity),
        requested_price=_optional_decimal_from_storage(row.requested_price),
        state=ExecutionState(row.state),
        raw_status_code=row.raw_status_code,
        metadata_json=row.metadata_json,
        created_at=datetime_from_storage(row.created_at),
        updated_at=datetime_from_storage(row.updated_at),
        exchange_created_at=_optional_datetime_from_storage(row.exchange_created_at),
        exchange_updated_at=_optional_datetime_from_storage(row.exchange_updated_at),
    )


def execution_order_row(record: ExecutionOrderRecord) -> ExecutionOrderRow:
    row = ExecutionOrderRow()
    row.execution_order_id = record.execution_order_id
    row.intent_id = record.intent_id
    row.client_order_id = record.client_order_id
    row.exchange_order_id = record.exchange_order_id
    row.pair = record.pair
    row.side = record.side.value
    row.order_type = record.order_type.value
    row.requested_quantity = decimal_to_storage(record.requested_quantity)
    row.requested_price = _optional_decimal_to_storage(record.requested_price)
    row.filled_quantity = decimal_to_storage(record.filled_quantity)
    row.average_fill_price = _optional_decimal_to_storage(record.average_fill_price)
    row.state = record.state.value
    row.raw_status_code = record.raw_status_code
    row.metadata_json = redacted_execution_metadata_json(record.metadata_json)
    row.created_at = datetime_to_storage(record.created_at)
    row.updated_at = datetime_to_storage(record.updated_at)
    row.exchange_created_at = _optional_datetime_to_storage(record.exchange_created_at)
    row.exchange_updated_at = _optional_datetime_to_storage(record.exchange_updated_at)
    return row


def execution_order_record_from_row(row: ExecutionOrderRow) -> ExecutionOrderRecord:
    return ExecutionOrderRecord(
        execution_order_id=row.execution_order_id,
        intent_id=row.intent_id,
        client_order_id=row.client_order_id,
        exchange_order_id=row.exchange_order_id,
        pair=row.pair,
        side=PositionSide(row.side),
        order_type=OrderType(row.order_type),
        requested_quantity=decimal_from_storage(row.requested_quantity),
        requested_price=_optional_decimal_from_storage(row.requested_price),
        filled_quantity=decimal_from_storage(row.filled_quantity),
        average_fill_price=_optional_decimal_from_storage(row.average_fill_price),
        state=ExecutionState(row.state),
        raw_status_code=row.raw_status_code,
        metadata_json=row.metadata_json,
        created_at=datetime_from_storage(row.created_at),
        updated_at=datetime_from_storage(row.updated_at),
        exchange_created_at=_optional_datetime_from_storage(row.exchange_created_at),
        exchange_updated_at=_optional_datetime_from_storage(row.exchange_updated_at),
    )


def execution_fill_row(record: ExecutionFillRecord) -> ExecutionFillRow:
    row = ExecutionFillRow()
    row.execution_fill_id = record.execution_fill_id
    row.intent_id = record.intent_id
    row.execution_order_id = record.execution_order_id
    row.exchange_order_id = record.exchange_order_id
    row.pair = record.pair
    row.side = record.side.value
    row.quantity = decimal_to_storage(record.quantity)
    row.price = decimal_to_storage(record.price)
    row.fee_asset = record.fee_asset
    row.fee_amount = _optional_decimal_to_storage(record.fee_amount)
    row.metadata_json = redacted_execution_metadata_json(record.metadata_json)
    row.filled_at = datetime_to_storage(record.filled_at)
    return row


def execution_fill_record_from_row(row: ExecutionFillRow) -> ExecutionFillRecord:
    return ExecutionFillRecord(
        execution_fill_id=row.execution_fill_id,
        intent_id=row.intent_id,
        execution_order_id=row.execution_order_id,
        exchange_order_id=row.exchange_order_id,
        pair=row.pair,
        side=PositionSide(row.side),
        quantity=decimal_from_storage(row.quantity),
        price=decimal_from_storage(row.price),
        fee_asset=row.fee_asset,
        fee_amount=_optional_decimal_from_storage(row.fee_amount),
        metadata_json=row.metadata_json,
        filled_at=datetime_from_storage(row.filled_at),
    )


def execution_event_row(record: ExecutionEventRecord) -> ExecutionEventRow:
    row = ExecutionEventRow()
    row.intent_id = record.intent_id
    row.event_type = record.event_type.value
    row.state = record.state.value
    row.message = record.message
    row.raw_status_code = record.raw_status_code
    row.metadata_json = redacted_execution_metadata_json(record.metadata_json)
    row.occurred_at = datetime_to_storage(record.occurred_at)
    return row


def execution_event_record_from_row(row: ExecutionEventRow) -> ExecutionEventRecord:
    return ExecutionEventRecord(
        event_id=row.event_id,
        intent_id=row.intent_id,
        event_type=ExecutionEventType(row.event_type),
        state=ExecutionState(row.state),
        message=row.message,
        raw_status_code=row.raw_status_code,
        metadata_json=row.metadata_json,
        occurred_at=datetime_from_storage(row.occurred_at),
    )


def _optional_decimal_to_storage(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return decimal_to_storage(value)


def _optional_decimal_from_storage(value: str | None) -> Decimal | None:
    if value is None:
        return None
    return decimal_from_storage(value)


def _optional_datetime_to_storage(value: datetime | None) -> str | None:
    if value is None:
        return None
    return datetime_to_storage(value)


def _optional_datetime_from_storage(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime_from_storage(value)
