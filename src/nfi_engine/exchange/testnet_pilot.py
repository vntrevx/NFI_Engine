from __future__ import annotations

from hashlib import sha256
from typing import Final, assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import TradingMode

from .testnet_pilot_checks import (
    credential_check,
    live_lock_check,
    permission_check,
    profile_check,
    strategy_check,
    testnet_check,
)
from .testnet_pilot_models import (
    PILOT_STATES,
    PILOT_TRANSITIONS,
    ControlDraft,
    TestnetPilotControl,
    TestnetPilotControlStatus,
    TestnetPilotExecutionPlan,
    TestnetPilotReport,
    pass_control,
)
from .testnet_pilot_safety import circuit_breaker_check, reconciliation_gate_check

CLIENT_ID_DIGEST_LENGTH: Final = 16


def build_testnet_pilot_report(*, settings: RuntimeSettings) -> TestnetPilotReport:
    client_order_id = build_testnet_client_order_id(settings=settings)
    controls = (
        profile_check(settings),
        live_lock_check(settings),
        testnet_check(settings),
        credential_check(settings),
        permission_check(settings),
        reconciliation_gate_check(settings),
        circuit_breaker_check(settings),
        strategy_check(settings),
        _idempotency_check(),
        _state_machine_check(),
    )
    blockers = tuple(
        control.code for control in controls if control.status is TestnetPilotControlStatus.BLOCK
    )
    return TestnetPilotReport(
        exchange=settings.exchange.name,
        trading_mode=settings.exchange.trading_mode.value,
        testnet=settings.exchange.testnet,
        pilot_ready=not blockers,
        live_money_orders_enabled=False,
        sample_client_order_id=client_order_id,
        execution_plan=build_testnet_execution_plan(client_order_id=client_order_id),
        states=PILOT_STATES,
        controls=controls,
        blockers=blockers,
    )


def build_testnet_client_order_id(*, settings: RuntimeSettings) -> str:
    raw_key = "|".join(
        (
            settings.exchange.name,
            settings.exchange.trading_mode.value,
            settings.strategy.name,
            _first_pair(settings),
            "testnet-pilot-v1",
        ),
    )
    digest = sha256(raw_key.encode("utf-8")).hexdigest()[:CLIENT_ID_DIGEST_LENGTH]
    return f"nfi-tn-{digest}"


def build_testnet_execution_plan(*, client_order_id: str) -> TestnetPilotExecutionPlan:
    return TestnetPilotExecutionPlan(
        client_order_id=client_order_id,
        dry_run_preview_required=True,
        kill_switch_required=True,
        reconciliation_required=True,
        idempotency_key_source="exchange|trading_mode|strategy|first_pair|pilot_version",
        transitions=PILOT_TRANSITIONS,
    )


def _idempotency_check() -> TestnetPilotControl:
    return pass_control(
        ControlDraft(
            stage="idempotency",
            code="TESTNET_PILOT_IDEMPOTENCY_READY",
            message="Stable client order ids are generated before submission.",
            next_action="Reuse the same client order id for retry-safe testnet submissions.",
        ),
    )


def _state_machine_check() -> TestnetPilotControl:
    return pass_control(
        ControlDraft(
            stage="order_state_machine",
            code="TESTNET_PILOT_STATE_MACHINE_READY",
            message="Pilot report exposes every required order lifecycle state.",
            next_action="Verify exchange adapters map raw order states into this state set.",
        ),
    )


def _first_pair(settings: RuntimeSettings) -> str:
    for raw_pair in settings.pairlist.whitelist.split(","):
        pair = raw_pair.strip()
        if pair != "":
            return pair
    match settings.exchange.trading_mode:
        case TradingMode.FUTURES:
            return "BTC/USDT:USDT"
        case TradingMode.SPOT:
            return "BTC/USDT"
        case unreachable:
            assert_never(unreachable)
