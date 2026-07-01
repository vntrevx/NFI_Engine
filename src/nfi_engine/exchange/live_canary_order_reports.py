from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal

from nfi_engine.config import RuntimeSettings
from nfi_engine.exchange.live_canary_order_models import (
    LiveCanaryOrderBlocker,
    LiveCanaryOrderEvent,
    LiveCanaryOrderEventType,
    LiveCanaryOrderReport,
)


def blocked_report(
    settings: RuntimeSettings,
    preview_hash: str,
    reference_price_usdt: Decimal,
    blockers: tuple[str, ...],
    now: datetime,
) -> LiveCanaryOrderReport:
    event = LiveCanaryOrderEvent(
        event_type=LiveCanaryOrderEventType.BLOCKED,
        message="live canary execution blocked before adapter construction",
        occurred_at=now,
    )
    return _report(settings, preview_hash, None, reference_price_usdt, None, (event,), blockers)


def duplicate_report(  # noqa: PLR0913
    settings: RuntimeSettings,
    preview_hash: str,
    client_order_id: str,
    reference_price_usdt: Decimal,
    quantity: Decimal,
    now: datetime,
) -> LiveCanaryOrderReport:
    event = LiveCanaryOrderEvent(
        event_type=LiveCanaryOrderEventType.BLOCKED,
        message="duplicate live canary confirmation rejected before exchange call",
        occurred_at=now,
    )
    return _report(
        settings,
        preview_hash,
        client_order_id,
        reference_price_usdt,
        quantity,
        (event,),
        (LiveCanaryOrderBlocker.LEDGER_DUPLICATE.value,),
        duplicate_rejected=True,
    )


def execution_report(  # noqa: PLR0913
    settings: RuntimeSettings,
    preview_hash: str,
    client_order_id: str,
    reference_price_usdt: Decimal,
    quantity: Decimal,
    events: list[LiveCanaryOrderEvent],
    blockers: tuple[str, ...],
    *,
    entry_order_id: str | None = None,
    exit_order_id: str | None = None,
) -> LiveCanaryOrderReport:
    return _report(
        settings,
        preview_hash,
        client_order_id,
        reference_price_usdt,
        quantity,
        tuple(events),
        blockers,
        entry_order_id=entry_order_id,
        exit_order_id=exit_order_id,
    )


def metadata_json(preview_hash: str, reference_price_usdt: Decimal) -> str:
    return json.dumps(
        {"preview_hash": preview_hash, "reference_price_usdt": str(reference_price_usdt)},
        separators=(",", ":"),
        sort_keys=True,
    )


def _report(  # noqa: PLR0913
    settings: RuntimeSettings,
    preview_hash: str,
    client_order_id: str | None,
    reference_price_usdt: Decimal,
    quantity: Decimal | None,
    events: tuple[LiveCanaryOrderEvent, ...],
    blockers: tuple[str, ...],
    *,
    duplicate_rejected: bool = False,
    entry_order_id: str | None = None,
    exit_order_id: str | None = None,
) -> LiveCanaryOrderReport:
    return LiveCanaryOrderReport(
        ready=blockers == (),
        executed=blockers == (),
        live_money_orders_enabled=blockers == (),
        duplicate_rejected=duplicate_rejected,
        exchange=settings.exchange.name,
        production=not settings.exchange.testnet,
        preview_hash=preview_hash,
        client_order_id=client_order_id,
        pair=settings.live_canary.pair,
        canary_notional_usdt=settings.live_canary.canary_notional_usdt,
        reference_price_usdt=reference_price_usdt,
        quantity=quantity,
        entry_order_id=entry_order_id,
        exit_order_id=exit_order_id,
        reconciliation_status="clear" if blockers == () else "blocked",
        events=events,
        blockers=blockers,
    )
