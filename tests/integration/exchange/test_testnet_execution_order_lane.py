from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import httpx
import pytest

from nfi_engine.config.models import (
    CircuitBreakerSettings,
    ExchangeSettings,
    ReconciliationSettings,
    RuntimeSettings,
    StrategySettings,
)
from nfi_engine.domain import OrderState, TradingMode
from nfi_engine.exchange.binance_order_test import BinanceFuturesOrderTestAdapter
from nfi_engine.exchange.errors import ExchangeErrorCode
from nfi_engine.exchange.permissions import ExchangeApiPermissionState
from nfi_engine.exchange.testnet_execution import run_testnet_execution_dry_run
from nfi_engine.exchange.testnet_pilot_models import TestnetPilotState as PilotState

pytestmark = pytest.mark.anyio

FIXED_TIMESTAMP_MS = 1_700_000_000_000
API_KEY = "test-binance-key"
SIGNING_KEY = "test-binance-signing-key"


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_binance_futures_order_test_lane_reports_submitted_acknowledged_state() -> None:
    # Given
    client = RecordingPostClient()
    adapter = _order_test_adapter(client)

    # When
    report = await run_testnet_execution_dry_run(
        _testnet_settings(),
        order_test_adapter=adapter,
    )

    # Then
    assert report.execution_ready is True
    assert report.live_money_orders_enabled is False
    assert report.live_exchange_observed is False
    assert report.submitted_order_id == f"binance-test-{FIXED_TIMESTAMP_MS}"
    assert report.adapter_order_state is OrderState.OPEN
    assert report.final_state is PilotState.ACKNOWLEDGED
    assert tuple(event.state for event in report.events) == (
        PilotState.INTENT_CREATED,
        PilotState.RISK_CHECKED,
        PilotState.SUBMITTED,
        PilotState.ACKNOWLEDGED,
    )
    assert client.requests
    assert client.requests[0].url.host == "demo-fapi.binance.com"
    dumped = report.model_dump_json()
    assert API_KEY not in dumped
    assert SIGNING_KEY not in dumped


async def test_binance_futures_order_test_lane_redacts_auth_failure_and_skips_ack() -> None:
    # Given
    client = RecordingPostClient(status_code=401)
    adapter = _order_test_adapter(client)

    # When
    report = await run_testnet_execution_dry_run(
        _testnet_settings(),
        order_test_adapter=adapter,
    )

    # Then
    assert report.execution_ready is False
    assert report.live_money_orders_enabled is False
    assert report.submitted_order_id is None
    assert report.adapter_order_state is None
    assert report.final_state is PilotState.SUBMITTED
    assert report.blockers == (ExchangeErrorCode.EXCHANGE_AUTH_FAILED.value,)
    assert PilotState.ACKNOWLEDGED not in tuple(event.state for event in report.events)
    dumped = report.model_dump_json()
    assert API_KEY not in dumped
    assert SIGNING_KEY not in dumped


async def test_testnet_execution_dry_run_blocks_manual_halt_before_adapter(
    tmp_path: Path,
) -> None:
    # Given
    manual_halt_file = tmp_path / "manual-halt.flag"
    manual_halt_file.touch()
    client = RecordingPostClient()
    adapter = _order_test_adapter(client)

    # When
    report = await run_testnet_execution_dry_run(
        _testnet_settings(manual_halt_file=manual_halt_file),
        order_test_adapter=adapter,
    )

    # Then
    assert client.requests == []
    assert report.execution_ready is False
    assert report.submitted_order_id is None
    assert report.adapter_order_state is None
    assert report.final_state is PilotState.RISK_CHECKED
    assert tuple(event.state for event in report.events) == (
        PilotState.INTENT_CREATED,
        PilotState.RISK_CHECKED,
    )
    assert report.blockers == ("manual_halt",)


def _testnet_settings(*, manual_halt_file: Path | None = None) -> RuntimeSettings:
    halt_file = ".runtime/manual-halt.flag" if manual_halt_file is None else str(manual_halt_file)
    return RuntimeSettings(
        exchange=ExchangeSettings(
            name="binance",
            trading_mode=TradingMode.FUTURES,
            testnet=True,
            api_key=API_KEY,
            api_secret=SIGNING_KEY,
            permission_read=ExchangeApiPermissionState.ENABLED,
            permission_trade=ExchangeApiPermissionState.ENABLED,
            permission_futures=ExchangeApiPermissionState.ENABLED,
            permission_withdrawal=ExchangeApiPermissionState.DISABLED,
            permission_ip_allowlist=ExchangeApiPermissionState.ENABLED,
        ),
        strategy=StrategySettings(
            name="X7NativeStrategy",
            module="nfi_engine.strategy.nfi_x7:X7NativeStrategy",
        ),
        reconciliation=ReconciliationSettings(
            required=True,
            fixture_path="tests/fixtures/exchange/reconcile_match.json",
        ),
        circuit_breakers=CircuitBreakerSettings(
            manual_halt_file=halt_file,
        ),
    )


def _order_test_adapter(client: RecordingPostClient) -> BinanceFuturesOrderTestAdapter:
    return BinanceFuturesOrderTestAdapter(
        api_key=API_KEY,
        api_secret=SIGNING_KEY,
        client=client,
        timestamp_ms=_fixed_timestamp_ms,
    )


def _fixed_timestamp_ms() -> int:
    return FIXED_TIMESTAMP_MS


@dataclass(frozen=True, slots=True)
class RecordingPostClient:
    status_code: int = 200
    requests: list[httpx.Request] = field(default_factory=list)

    async def post(
        self,
        url: str,
        *,
        params: tuple[tuple[str, str], ...],
        headers: Mapping[str, str],
    ) -> httpx.Response:
        request = httpx.Request(
            "POST",
            f"https://demo-fapi.binance.com{url}",
            params=params,
            headers=headers,
        )
        self.requests.append(request)
        return httpx.Response(self.status_code, json={})
