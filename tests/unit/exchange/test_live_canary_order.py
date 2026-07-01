from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx
import pytest

from nfi_engine.config import load_runtime_settings
from nfi_engine.domain import OrderState, OrderType, PositionSide
from nfi_engine.exchange.binance import BINANCE_FAPI_BASE_URL
from nfi_engine.exchange.live_canary_binance import BinanceFuturesLiveCanaryClient
from nfi_engine.exchange.live_canary_hash import live_canary_preview_hash
from nfi_engine.exchange.live_canary_order import (
    LIVE_CANARY_EXECUTION_PHRASE,
    run_live_canary_order,
)
from nfi_engine.exchange.live_canary_order_models import (
    LiveCanaryClientError,
    LiveCanaryExchangeOrder,
    LiveCanaryOrderBlocker,
    LiveCanaryOrderEventType,
    LiveCanaryOrderRequest,
)
from nfi_engine.execution import ExecutionEventType
from nfi_engine.persistence import create_persistence_database
from nfi_engine.persistence.repositories import ExecutionEventRepository
from nfi_engine.persistence.session import PersistenceDatabase

pytestmark = pytest.mark.anyio

FIXTURE = Path("tests/fixtures/config/live-canary-preview.yaml")
NOW = datetime(2026, 6, 30, 0, 2, tzinfo=UTC)
REFERENCE_PRICE = Decimal(100)
DUMMY_PRIVATE_VALUE = "local-live-canary-secret"
LOCAL_API_PRIVATE_VALUE = "local-secret"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
async def database(tmp_path: Path) -> AsyncIterator[PersistenceDatabase]:
    database = create_persistence_database(f"sqlite+aiosqlite:///{tmp_path / 'canary.sqlite'}")
    try:
        yield database
    finally:
        await database.dispose()


async def test_live_canary_order_executes_entry_exit_and_writes_events(
    database: PersistenceDatabase,
) -> None:
    # Given: a fake production client and an explicit preview hash confirmation.
    settings = load_runtime_settings(FIXTURE)
    preview_hash = live_canary_preview_hash(settings)
    client = _FakeLiveCanaryClient(fetch_state=OrderState.FILLED)

    # When
    report = await run_live_canary_order(
        settings=settings,
        database=database,
        preview_hash=preview_hash,
        confirmation_hash=preview_hash,
        confirmation_phrase=LIVE_CANARY_EXECUTION_PHRASE,
        reference_price_usdt=REFERENCE_PRICE,
        client=client,
        now=NOW,
    )

    # Then
    assert report.ready is True
    assert report.executed is True
    assert report.live_money_orders_enabled is True
    assert report.quantity == Decimal("0.075")
    assert report.entry_order_id == "entry-fetch"
    assert report.exit_order_id == "exit-submit"
    assert report.blockers == ()
    assert [request.reduce_only for request in client.submitted] == [False, True]
    assert client.submitted[1].side is PositionSide.SHORT
    assert client.fetched[0].client_order_id == report.client_order_id
    stored_events = await _stored_events(database, preview_hash)
    assert ExecutionEventType.ORDER_SUBMITTED in stored_events
    assert ExecutionEventType.FILL_RECORDED in stored_events
    assert ExecutionEventType.RECONCILED in stored_events


async def test_live_canary_order_rejects_duplicate_confirmation_before_exchange_call(
    database: PersistenceDatabase,
) -> None:
    # Given: a completed canary confirmation in the ledger.
    settings = load_runtime_settings(FIXTURE)
    preview_hash = live_canary_preview_hash(settings)
    first_client = _FakeLiveCanaryClient(fetch_state=OrderState.FILLED)
    duplicate_client = _FakeLiveCanaryClient(fetch_state=OrderState.FILLED)

    # When
    first = await run_live_canary_order(
        settings=settings,
        database=database,
        preview_hash=preview_hash,
        confirmation_hash=preview_hash,
        confirmation_phrase=LIVE_CANARY_EXECUTION_PHRASE,
        reference_price_usdt=REFERENCE_PRICE,
        client=first_client,
        now=NOW,
    )
    duplicate = await run_live_canary_order(
        settings=settings,
        database=database,
        preview_hash=preview_hash,
        confirmation_hash=preview_hash,
        confirmation_phrase=LIVE_CANARY_EXECUTION_PHRASE,
        reference_price_usdt=REFERENCE_PRICE,
        client=duplicate_client,
        now=NOW,
    )

    # Then
    assert first.ready is True
    assert duplicate.ready is False
    assert duplicate.duplicate_rejected is True
    assert duplicate.blockers == (LiveCanaryOrderBlocker.LEDGER_DUPLICATE.value,)
    assert duplicate_client.submitted == []
    assert duplicate_client.fetched == []


async def test_live_canary_order_blocks_hash_mismatch_before_adapter_construction(
    database: PersistenceDatabase,
) -> None:
    # Given
    settings = load_runtime_settings(FIXTURE)
    preview_hash = live_canary_preview_hash(settings)
    client = _FakeLiveCanaryClient(fetch_state=OrderState.FILLED)

    # When
    report = await run_live_canary_order(
        settings=settings,
        database=database,
        preview_hash="bad-hash",
        confirmation_hash=preview_hash,
        confirmation_phrase=LIVE_CANARY_EXECUTION_PHRASE,
        reference_price_usdt=REFERENCE_PRICE,
        client=client,
        now=NOW,
    )

    # Then
    assert report.ready is False
    assert LiveCanaryOrderBlocker.PREVIEW_HASH_MISMATCH.value in report.blockers
    assert client.submitted == []
    assert client.fetched == []


async def test_live_canary_order_blocks_partial_fill_until_reconciliation(
    database: PersistenceDatabase,
) -> None:
    # Given
    settings = load_runtime_settings(FIXTURE)
    preview_hash = live_canary_preview_hash(settings)
    client = _FakeLiveCanaryClient(fetch_state=OrderState.PARTIALLY_FILLED)

    # When
    report = await run_live_canary_order(
        settings=settings,
        database=database,
        preview_hash=preview_hash,
        confirmation_hash=preview_hash,
        confirmation_phrase=LIVE_CANARY_EXECUTION_PHRASE,
        reference_price_usdt=REFERENCE_PRICE,
        client=client,
        now=NOW,
    )

    # Then
    assert report.ready is False
    assert report.entry_order_id == "entry-fetch"
    assert report.exit_order_id == "exit-submit"
    assert report.blockers == (LiveCanaryOrderBlocker.PARTIAL_FILL.value,)
    assert len(client.submitted) == 2
    assert [request.reduce_only for request in client.submitted] == [False, True]
    assert client.submitted[1].quantity == Decimal("0.0375")
    assert client.fetched[0].client_order_id == report.client_order_id
    assert report.events[-1].event_type is LiveCanaryOrderEventType.BLOCKED


async def test_live_canary_order_redacts_exchange_rejection_messages(
    database: PersistenceDatabase,
) -> None:
    # Given
    settings = load_runtime_settings(FIXTURE)
    preview_hash = live_canary_preview_hash(settings)
    client = _FakeLiveCanaryClient(
        fetch_state=OrderState.FILLED,
        failure=LiveCanaryClientError(
            "LIVE_CANARY_EXCHANGE_AUTH_FAILED",
            f"rejected signature for {DUMMY_PRIVATE_VALUE}",
        ),
    )

    # When
    report = await run_live_canary_order(
        settings=settings,
        database=database,
        preview_hash=preview_hash,
        confirmation_hash=preview_hash,
        confirmation_phrase=LIVE_CANARY_EXECUTION_PHRASE,
        reference_price_usdt=REFERENCE_PRICE,
        client=client,
        now=NOW,
    )

    # Then
    assert report.ready is False
    assert report.blockers == ("LIVE_CANARY_EXCHANGE_AUTH_FAILED",)
    assert DUMMY_PRIVATE_VALUE not in report.model_dump_json()
    assert "REDACTED" in report.events[-1].message


async def test_binance_live_canary_client_uses_signed_production_order_endpoint() -> None:
    # Given
    http_client = _FakeBinanceHttpClient()
    client = BinanceFuturesLiveCanaryClient(
        api_key="local-key",
        api_secret=LOCAL_API_PRIVATE_VALUE,
        client=http_client,
        timestamp_ms=lambda: 123456,
    )
    request = LiveCanaryOrderRequest(
        client_order_id="nfi-lc-test",
        pair="BTC/USDT:USDT",
        side=PositionSide.LONG,
        order_type=OrderType.MARKET,
        quantity=Decimal("0.075"),
        leverage=Decimal(2),
        reduce_only=False,
    )

    # When
    order = await client.submit_order(request)
    fetched = await client.fetch_order(request)

    # Then
    assert client.base_url == BINANCE_FAPI_BASE_URL
    assert order.exchange_order_id == "binance-live-1"
    assert fetched.exchange_order_id == "binance-live-1"
    assert http_client.calls[0][0] == "POST"
    assert http_client.calls[1][0] == "GET"
    assert all(call[1] == "/fapi/v1/order" for call in http_client.calls)
    assert ("newClientOrderId", "nfi-lc-test") in http_client.calls[0][2]
    assert ("origClientOrderId", "nfi-lc-test") in http_client.calls[1][2]
    assert any(key == "signature" for key, _value in http_client.calls[0][2])


async def _stored_events(
    database: PersistenceDatabase,
    preview_hash: str,
) -> tuple[ExecutionEventType, ...]:
    intent_id = f"live-canary-{preview_hash[:16]}"
    async with database.session() as session:
        records = await ExecutionEventRepository(session).list_for_intent(intent_id, limit=20)
    return tuple(record.event_type for record in records)


class _FakeLiveCanaryClient:
    fetch_state: OrderState
    failure: LiveCanaryClientError | None

    def __init__(
        self,
        *,
        fetch_state: OrderState,
        failure: LiveCanaryClientError | None = None,
    ) -> None:
        self.fetch_state = fetch_state
        self.failure = failure
        self.submitted: list[LiveCanaryOrderRequest] = []
        self.fetched: list[LiveCanaryOrderRequest] = []

    async def submit_order(self, request: LiveCanaryOrderRequest) -> LiveCanaryExchangeOrder:
        if self.failure is not None:
            raise self.failure
        self.submitted.append(request)
        if request.reduce_only:
            return _order("exit-submit", request, OrderState.FILLED)
        return _order("entry-submit", request, OrderState.OPEN, filled_quantity=Decimal(0))

    async def fetch_order(self, request: LiveCanaryOrderRequest) -> LiveCanaryExchangeOrder:
        self.fetched.append(request)
        filled_quantity = (
            request.quantity if self.fetch_state is OrderState.FILLED else request.quantity / 2
        )
        return _order("entry-fetch", request, self.fetch_state, filled_quantity=filled_quantity)


class _FakeBinanceHttpClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, tuple[tuple[str, str], ...]]] = []

    async def post(
        self,
        url: str,
        *,
        params: tuple[tuple[str, str], ...],
        headers: object,
    ) -> httpx.Response:
        assert headers is not None
        self.calls.append(("POST", url, params))
        return _binance_response()

    async def get(
        self,
        url: str,
        *,
        params: tuple[tuple[str, str], ...],
        headers: object,
    ) -> httpx.Response:
        assert headers is not None
        self.calls.append(("GET", url, params))
        return _binance_response()


def _binance_response() -> httpx.Response:
    return httpx.Response(
        200,
        json={
            "orderId": "binance-live-1",
            "clientOrderId": "nfi-lc-test",
            "symbol": "BTCUSDT",
            "side": "BUY",
            "type": "MARKET",
            "status": "FILLED",
            "origQty": "0.075",
            "executedQty": "0.075",
            "avgPrice": "100",
            "reduceOnly": False,
        },
    )


def _order(
    exchange_order_id: str,
    request: LiveCanaryOrderRequest,
    state: OrderState,
    *,
    filled_quantity: Decimal | None = None,
) -> LiveCanaryExchangeOrder:
    quantity = request.quantity if filled_quantity is None else filled_quantity
    return LiveCanaryExchangeOrder(
        exchange_order_id=exchange_order_id,
        client_order_id=request.client_order_id,
        pair=request.pair,
        side=request.side,
        order_type=OrderType.MARKET,
        state=state,
        quantity=request.quantity,
        filled_quantity=quantity,
        average_price=REFERENCE_PRICE if quantity > 0 else None,
        reduce_only=request.reduce_only,
        raw_status_code=state.value,
    )
