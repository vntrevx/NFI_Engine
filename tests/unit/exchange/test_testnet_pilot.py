from __future__ import annotations

from nfi_engine.config.models import (
    CircuitBreakerSettings,
    EngineSettings,
    ExchangeSettings,
    ReconciliationSettings,
    RuntimeSettings,
    StrategySettings,
)
from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.exchange.permissions import ExchangeApiPermissionState
from nfi_engine.exchange.testnet_pilot import (
    build_testnet_client_order_id,
    build_testnet_pilot_report,
)


def test_testnet_pilot_blocks_when_credentials_and_hardening_are_missing() -> None:
    # Given
    settings = RuntimeSettings(
        exchange=ExchangeSettings(name="bybit", trading_mode=TradingMode.FUTURES, testnet=True),
    )

    # When
    report = build_testnet_pilot_report(settings=settings)

    # Then
    assert report.pilot_ready is False
    assert report.live_money_orders_enabled is False
    assert "TESTNET_PILOT_CREDENTIALS_MISSING" in report.blockers
    assert "TESTNET_PILOT_X7_NATIVE_REQUIRED" in report.blockers
    assert report.sample_client_order_id.startswith("nfi-tn-")


def test_testnet_pilot_passes_for_hardened_testnet_x7_settings() -> None:
    # Given
    settings = _hardened_settings()

    # When
    report = build_testnet_pilot_report(settings=settings)

    # Then
    assert report.pilot_ready is True
    assert report.blockers == ()
    assert report.live_money_orders_enabled is False
    assert {state.value for state in report.states} >= {
        "intent_created",
        "partially_filled",
        "reconciled",
    }


def test_testnet_pilot_client_order_id_is_stable_and_secret_free() -> None:
    # Given
    settings = _hardened_settings().model_copy(
        update={
            "exchange": _hardened_settings().exchange.model_copy(
                update={"api_key": "secret-key", "api_secret": "secret-value"},
            ),
        },
    )

    # When
    first = build_testnet_client_order_id(settings=settings)
    second = build_testnet_client_order_id(settings=settings)

    # Then
    assert first == second
    assert "secret" not in first
    assert first.startswith("nfi-tn-")


def test_testnet_pilot_blocks_live_trading_even_with_hardened_controls() -> None:
    # Given
    settings = _hardened_settings().model_copy(
        update={"engine": EngineSettings(live_trading=True)},
    )

    # When
    report = build_testnet_pilot_report(settings=settings)

    # Then
    assert report.pilot_ready is False
    assert "TESTNET_PILOT_LIVE_TRADING_BLOCKED" in report.blockers
    assert report.live_money_orders_enabled is False


def _hardened_settings() -> RuntimeSettings:
    return RuntimeSettings(
        exchange=ExchangeSettings(
            name="binance",
            trading_mode=TradingMode.FUTURES,
            margin_mode=MarginMode.ISOLATED,
            testnet=True,
            api_key="key",
            api_secret="secret",  # noqa: S106 - test-only placeholder.
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
        circuit_breakers=CircuitBreakerSettings(manual_halt_file=".runtime/manual-halt.flag"),
    )
