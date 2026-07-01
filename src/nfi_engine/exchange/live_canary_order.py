from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import PositionSide, TradingPair
from nfi_engine.exchange.live_canary import build_live_canary_preview
from nfi_engine.exchange.live_canary_binance import BinanceFuturesLiveCanaryClient
from nfi_engine.exchange.live_canary_hash import live_canary_preview_hash
from nfi_engine.exchange.live_canary_ledger import reserve_live_canary_intent
from nfi_engine.exchange.live_canary_order_flow import execute_live_canary_flow
from nfi_engine.exchange.live_canary_order_models import (
    LiveCanaryExecutionClient,
    LiveCanaryOrderBlocker,
    LiveCanaryOrderReport,
    LiveCanaryOrderRequest,
)
from nfi_engine.exchange.live_canary_order_reports import (
    blocked_report,
    duplicate_report,
    metadata_json,
)
from nfi_engine.persistence.session import PersistenceDatabase

LIVE_CANARY_EXECUTION_PHRASE = "CONFIRM_LIVE_CANARY_ORDER"


async def run_live_canary_order(  # noqa: PLR0913
    *,
    settings: RuntimeSettings,
    database: PersistenceDatabase,
    preview_hash: str,
    confirmation_hash: str,
    confirmation_phrase: str,
    reference_price_usdt: Decimal,
    client: LiveCanaryExecutionClient | None = None,
    now: datetime | None = None,
) -> LiveCanaryOrderReport:
    observed_at = now or datetime.now(UTC)
    expected_hash = live_canary_preview_hash(settings)
    preview = build_live_canary_preview(settings=settings, now=observed_at)
    blocked = _preflight_blockers(
        preview_ready=preview.ready,
        preview_blockers=preview.blockers,
        expected_hash=expected_hash,
        preview_hash=preview_hash,
        confirmation_hash=confirmation_hash,
        confirmation_phrase=confirmation_phrase,
        reference_price_usdt=reference_price_usdt,
    )
    if blocked:
        return blocked_report(settings, expected_hash, reference_price_usdt, blocked, observed_at)

    await database.initialize()
    canary = settings.live_canary
    if (
        canary.pair is None
        or canary.order_type is None
        or canary.leverage is None
        or canary.canary_notional_usdt is None
    ):
        return blocked_report(
            settings,
            expected_hash,
            reference_price_usdt,
            (LiveCanaryOrderBlocker.PREVIEW_NOT_READY.value,),
            observed_at,
        )
    pair = TradingPair.parse(canary.pair, settings.exchange.trading_mode)
    notional = canary.canary_notional_usdt
    quantity = notional / reference_price_usdt
    client_order_id = f"nfi-lc-{expected_hash[:18]}"
    intent_id = f"live-canary-{expected_hash[:16]}"
    idempotency_key = f"live-canary:{expected_hash}"
    reserved = await reserve_live_canary_intent(
        database,
        intent_id=intent_id,
        idempotency_key=idempotency_key,
        client_order_id=client_order_id,
        pair=str(pair.normalized),
        order_type=canary.order_type,
        quantity=quantity,
        metadata_json=metadata_json(expected_hash, reference_price_usdt),
        now=observed_at,
    )
    if not reserved:
        return duplicate_report(
            settings, expected_hash, client_order_id, reference_price_usdt, quantity, observed_at
        )

    order_client = client or BinanceFuturesLiveCanaryClient.from_settings(settings)
    entry_request = LiveCanaryOrderRequest(
        client_order_id=client_order_id,
        pair=str(pair.normalized),
        side=PositionSide.LONG,
        order_type=canary.order_type,
        quantity=quantity,
        leverage=canary.leverage,
        reduce_only=False,
    )
    return await execute_live_canary_flow(
        settings=settings,
        database=database,
        order_client=order_client,
        expected_hash=expected_hash,
        client_order_id=client_order_id,
        intent_id=intent_id,
        reference_price_usdt=reference_price_usdt,
        quantity=quantity,
        entry_request=entry_request,
        observed_at=observed_at,
    )


def _preflight_blockers(  # noqa: PLR0913
    *,
    preview_ready: bool,
    preview_blockers: tuple[str, ...],
    expected_hash: str,
    preview_hash: str,
    confirmation_hash: str,
    confirmation_phrase: str,
    reference_price_usdt: Decimal,
) -> tuple[str, ...]:
    blockers: list[str] = []
    if not preview_ready:
        blockers.append(LiveCanaryOrderBlocker.PREVIEW_NOT_READY.value)
        blockers.extend(preview_blockers)
    if preview_hash != expected_hash or confirmation_hash != expected_hash:
        blockers.append(LiveCanaryOrderBlocker.PREVIEW_HASH_MISMATCH.value)
    if confirmation_phrase != LIVE_CANARY_EXECUTION_PHRASE:
        blockers.append(LiveCanaryOrderBlocker.EXECUTION_CONFIRMATION.value)
    if reference_price_usdt <= 0 or not reference_price_usdt.is_finite():
        blockers.append(LiveCanaryOrderBlocker.REFERENCE_PRICE.value)
    return tuple(blockers)
