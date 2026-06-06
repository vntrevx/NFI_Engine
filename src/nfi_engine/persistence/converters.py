from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal


def datetime_to_storage(value: datetime) -> str:
    return value.astimezone(UTC).isoformat()


def datetime_from_storage(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def decimal_to_storage(value: Decimal) -> str:
    return str(value)


def decimal_from_storage(value: str) -> Decimal:
    return Decimal(value)
