from __future__ import annotations

from datetime import datetime

from nfi_engine.config import RuntimeSettings
from nfi_engine.events import redact_text
from nfi_engine.exchange.live_canary_ledger import write_live_canary_event
from nfi_engine.exchange.live_canary_order_models import (
    LiveCanaryExchangeOrder,
    LiveCanaryOrderEvent,
    LiveCanaryOrderEventType,
)
from nfi_engine.persistence.session import PersistenceDatabase


async def append_live_canary_event(  # noqa: PLR0913
    database: PersistenceDatabase,
    intent_id: str,
    events: list[LiveCanaryOrderEvent],
    event_type: LiveCanaryOrderEventType,
    message: str,
    occurred_at: datetime,
) -> None:
    event = LiveCanaryOrderEvent(event_type=event_type, message=message, occurred_at=occurred_at)
    events.append(event)
    await write_live_canary_event(database, intent_id=intent_id, event=event)


async def append_live_canary_order_event(  # noqa: PLR0913
    database: PersistenceDatabase,
    intent_id: str,
    events: list[LiveCanaryOrderEvent],
    event_type: LiveCanaryOrderEventType,
    message: str,
    order: LiveCanaryExchangeOrder,
    occurred_at: datetime,
) -> None:
    event = LiveCanaryOrderEvent(
        event_type=event_type,
        message=message,
        state=order.state,
        exchange_order_id=order.exchange_order_id,
        occurred_at=occurred_at,
    )
    events.append(event)
    await write_live_canary_event(database, intent_id=intent_id, event=event)


def safe_exchange_message(settings: RuntimeSettings, message: str) -> str:
    return redact_text(message, secrets=_secrets(settings))


def _secrets(settings: RuntimeSettings) -> tuple[str, ...]:
    return tuple(
        secret
        for secret in (
            settings.exchange.api_key,
            settings.exchange.api_secret,
            settings.exchange.passphrase,
            settings.exchange.memo,
        )
        if secret
    )
