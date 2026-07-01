from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Final, assert_never

from nfi_engine.circuit_breakers import (
    CircuitBreakerSnapshot,
    evaluate_circuit_breakers,
)
from nfi_engine.circuit_breakers import (
    policy_from_runtime as circuit_policy_from_runtime,
)
from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import (
    Leverage,
    OrderType,
    PositionSide,
    Price,
    Quantity,
    TradingMode,
    TradingPair,
)
from nfi_engine.exchange.errors import ExchangeError
from nfi_engine.exchange.models import ExchangeOrder, ExchangeOrderRequest, Tick
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.exchange.testnet_execution_events import (
    testnet_execution_events_for_order,
    testnet_intent_events,
    testnet_pilot_state_from_order_state,
    testnet_pre_submission_events,
    testnet_submission_attempt_events,
)
from nfi_engine.exchange.testnet_execution_models import (
    TestnetExecutionReport,
    TestnetOrderTestAdapter,
)
from nfi_engine.exchange.testnet_pilot import build_testnet_pilot_report

__all__ = (
    "TestnetExecutionReport",
    "run_testnet_execution_dry_run",
    "testnet_execution_events_for_order",
    "testnet_pilot_state_from_order_state",
)

DEFAULT_EXECUTION_PRICE: Final = Decimal(100)
DEFAULT_EXECUTION_QUANTITY: Final = Decimal("0.10")
DEFAULT_EXECUTION_LEVERAGE: Final = "3"
DEFAULT_EXECUTION_AT: Final = datetime(2026, 1, 1, tzinfo=UTC)
DEFAULT_EXECUTION_EQUITY: Final = Decimal(1000)


async def run_testnet_execution_dry_run(
    settings: RuntimeSettings,
    *,
    order_test_adapter: TestnetOrderTestAdapter | None = None,
) -> TestnetExecutionReport:
    pilot_report = build_testnet_pilot_report(settings=settings)
    if not pilot_report.pilot_ready:
        return TestnetExecutionReport(
            exchange=pilot_report.exchange,
            trading_mode=pilot_report.trading_mode,
            testnet=pilot_report.testnet,
            execution_ready=False,
            live_money_orders_enabled=False,
            live_exchange_observed=False,
            client_order_id=pilot_report.sample_client_order_id,
            submitted_order_id=None,
            adapter_order_state=None,
            final_state=None,
            events=testnet_intent_events(),
            blockers=pilot_report.blockers,
        )

    decision = evaluate_circuit_breakers(
        policy=circuit_policy_from_runtime(settings),
        snapshot=CircuitBreakerSnapshot(
            realized_pnl_today=Decimal(0),
            equity_start=DEFAULT_EXECUTION_EQUITY,
            equity_current=DEFAULT_EXECUTION_EQUITY,
            consecutive_losses=0,
            latest_tick_at=DEFAULT_EXECUTION_AT,
            current_time=DEFAULT_EXECUTION_AT,
            api_error_count=0,
            observed_slippage_pct=Decimal(0),
            funding_rate=Decimal(0),
            manual_halt=False,
            rejected_order_count=0,
        ),
    )
    if decision.new_orders_blocked:
        events = testnet_pre_submission_events()
        return TestnetExecutionReport(
            exchange=pilot_report.exchange,
            trading_mode=pilot_report.trading_mode,
            testnet=pilot_report.testnet,
            execution_ready=False,
            live_money_orders_enabled=False,
            live_exchange_observed=False,
            client_order_id=pilot_report.sample_client_order_id,
            submitted_order_id=None,
            adapter_order_state=None,
            final_state=events[-1].state,
            events=events,
            blockers=tuple(trigger.kind.value for trigger in decision.triggered),
        )

    pair = _execution_pair(settings.exchange.trading_mode)
    request = ExchangeOrderRequest(
        pair=pair,
        side=PositionSide.LONG,
        order_type=OrderType.MARKET,
        quantity=Quantity(DEFAULT_EXECUTION_QUANTITY),
        price=None,
        leverage=Leverage.parse(DEFAULT_EXECUTION_LEVERAGE),
    )
    if order_test_adapter is None:
        observed_order = await _simulate_testnet_order(request)
    else:
        try:
            observed_order = await order_test_adapter.test_order(request)
        except ExchangeError as exc:
            events = testnet_submission_attempt_events()
            return TestnetExecutionReport(
                exchange=pilot_report.exchange,
                trading_mode=pilot_report.trading_mode,
                testnet=pilot_report.testnet,
                execution_ready=False,
                live_money_orders_enabled=False,
                live_exchange_observed=False,
                client_order_id=pilot_report.sample_client_order_id,
                submitted_order_id=None,
                adapter_order_state=None,
                final_state=events[-1].state,
                events=events,
                blockers=(exc.code.value,),
            )
    events = testnet_execution_events_for_order(observed_order)
    return TestnetExecutionReport(
        exchange=pilot_report.exchange,
        trading_mode=pilot_report.trading_mode,
        testnet=pilot_report.testnet,
        execution_ready=True,
        live_money_orders_enabled=False,
        live_exchange_observed=observed_order.live_exchange,
        client_order_id=pilot_report.sample_client_order_id,
        submitted_order_id=observed_order.order_id,
        adapter_order_state=observed_order.state,
        final_state=events[-1].state,
        events=events,
        blockers=(),
    )


async def _simulate_testnet_order(request: ExchangeOrderRequest) -> ExchangeOrder:
    simulator = DeterministicExchangeSimulator(
        ticks=(
            Tick(
                pair=request.pair,
                price=Price(DEFAULT_EXECUTION_PRICE),
                at=DEFAULT_EXECUTION_AT,
            ),
        ),
    )
    submitted_order = await simulator.create_order(request)
    return await simulator.fetch_order(
        order_id=submitted_order.order_id,
        pair=submitted_order.pair,
    )


def _execution_pair(trading_mode: TradingMode) -> TradingPair:
    match trading_mode:
        case TradingMode.FUTURES:
            return TradingPair.parse("BTC/USDT:USDT", trading_mode)
        case TradingMode.SPOT:
            return TradingPair.parse("BTC/USDT", trading_mode)
        case unreachable:
            assert_never(unreachable)
