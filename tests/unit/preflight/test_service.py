from __future__ import annotations

from pathlib import Path
from typing import Final

from nfi_engine.config import (
    CircuitBreakerSettings,
    EngineSettings,
    ExchangeSettings,
    RiskSettings,
    RuntimeSettings,
    StrategySettings,
    load_runtime_settings,
)
from nfi_engine.config.enums import RiskProfileName
from nfi_engine.config.models import ReconciliationSettings
from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.exchange.permissions import ExchangeApiPermissionState
from nfi_engine.preflight import PreflightCode, PreflightReport, PreflightStatus
from nfi_engine.preflight.service import run_preflight
from nfi_engine.ui.pages import render_settings_page

FIXTURE_API_VALUE: Final = "fixture-value"


def test_bybit_testnet_fixture_passes_readiness_checks() -> None:
    # Given: the futures paper config and Bybit testnet profile.
    config_path = Path("examples/futures-paper.yaml")
    settings = load_runtime_settings(config_path)

    # When: preflight runs without mutating runtime state.
    report = run_preflight(settings=settings, profile_name="bybit-testnet", config_path=config_path)

    # Then: no blocking checks remain.
    assert report.blocked is False
    assert _status(report, PreflightCode.CONFIG_VALID) is PreflightStatus.PASS
    assert _status(report, PreflightCode.PROFILE_COMPATIBLE) is PreflightStatus.PASS
    assert _status(report, PreflightCode.DOCKER_VOLUMES_READY) is PreflightStatus.PASS


def test_bybit_profile_accepts_registry_normalized_exchange_id() -> None:
    # Given: Bybit testnet settings using casing that the exchange registry normalizes.
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            name="ByBit",
            trading_mode=TradingMode.FUTURES,
            margin_mode=MarginMode.ISOLATED,
            testnet=True,
        ),
    )

    # When: preflight checks the Bybit profile compatibility.
    report = run_preflight(settings=settings, profile_name="bybit-testnet")

    # Then: profile compatibility is accepted through registry metadata.
    assert report.blocked is False
    assert _status(report, PreflightCode.PROFILE_COMPATIBLE) is PreflightStatus.PASS


def test_profile_config_mismatch_blocks_readiness() -> None:
    # Given: a spot config paired with the Bybit futures profile.
    config_path = Path("examples/spot-paper.yaml")
    settings = load_runtime_settings(config_path)

    # When: preflight checks profile compatibility.
    report = run_preflight(settings=settings, profile_name="bybit-testnet", config_path=config_path)

    # Then: the mismatch is blocking.
    assert report.blocked is True
    assert _status(report, PreflightCode.PROFILE_CONFIG_MISMATCH) is PreflightStatus.BLOCK


def test_public_api_bind_blocks_readiness() -> None:
    # Given: a config that asks the API to bind publicly.
    config_path = Path("tests/fixtures/config/api-public-bind.yaml")
    settings = load_runtime_settings(config_path)

    # When: preflight checks local bind safety.
    report = run_preflight(settings=settings, profile_name="local-paper", config_path=config_path)

    # Then: public bind is a blocking failure.
    assert report.blocked is True
    assert _status(report, PreflightCode.PUBLIC_BIND_NOT_ALLOWED) is PreflightStatus.BLOCK


def test_weak_production_token_blocks_readiness() -> None:
    # Given: production config with a weak token.
    config_path = Path("tests/fixtures/config/api-weak-token-prod.yaml")
    settings = load_runtime_settings(config_path)

    # When: preflight checks API auth strength.
    report = run_preflight(settings=settings, profile_name="local-paper", config_path=config_path)

    # Then: weak API auth is blocking.
    assert report.blocked is True
    assert _status(report, PreflightCode.WEAK_API_TOKEN) is PreflightStatus.BLOCK


def test_missing_database_parent_blocks_readiness() -> None:
    # Given: a config whose SQLite parent cannot be created.
    config_path = Path("tests/fixtures/config/preflight-missing-db.yaml")
    settings = load_runtime_settings(config_path)

    # When: preflight checks SQLite readiness.
    report = run_preflight(settings=settings, profile_name="local-paper", config_path=config_path)

    # Then: database storage readiness blocks start.
    assert report.blocked is True
    assert _status(report, PreflightCode.DB_PATH_MISSING) is PreflightStatus.BLOCK


def test_unwritable_log_path_blocks_readiness() -> None:
    # Given: a config whose notification log path cannot be created.
    config_path = Path("tests/fixtures/config/preflight-unwritable-log.yaml")
    settings = load_runtime_settings(config_path)

    # When: preflight checks writable log/report output.
    report = run_preflight(settings=settings, profile_name="local-paper", config_path=config_path)

    # Then: log path readiness blocks start.
    assert report.blocked is True
    assert _status(report, PreflightCode.LOG_PATH_NOT_WRITABLE) is PreflightStatus.BLOCK


def test_live_mode_blocks_readiness() -> None:
    # Given: a live-order config that loads but is out of milestone-one scope.
    config_path = Path("tests/fixtures/config/live-real-orders.yaml")
    settings = load_runtime_settings(config_path)

    # When: preflight checks live-order policy.
    report = run_preflight(settings=settings, profile_name="bybit-testnet", config_path=config_path)

    # Then: live mode is a blocking failure.
    assert report.blocked is True
    assert _status(report, PreflightCode.LIVE_TRADING_OUT_OF_SCOPE) is PreflightStatus.BLOCK


def test_live_mode_surfaces_hardening_blockers() -> None:
    # Given: a confirmed live config with incomplete live hardening metadata.
    config_path = Path("tests/fixtures/config/live-real-orders.yaml")
    settings = load_runtime_settings(config_path)

    # When: preflight checks live-order readiness.
    report = run_preflight(settings=settings, profile_name="bybit-testnet", config_path=config_path)

    # Then: live execution remains blocked and the missing hardening steps are visible.
    assert report.blocked is True
    assert _status(report, PreflightCode.LIVE_EXCHANGE_CREDENTIALS) is PreflightStatus.PASS
    assert _status(report, PreflightCode.LIVE_PERMISSION_HARDENING) is PreflightStatus.BLOCK
    assert _status(report, PreflightCode.LIVE_RECONCILIATION_HARDENING) is PreflightStatus.BLOCK
    assert _status(report, PreflightCode.LIVE_CIRCUIT_BREAKER_HARDENING) is PreflightStatus.BLOCK
    assert _status(report, PreflightCode.LIVE_STRATEGY_HARDENING) is PreflightStatus.BLOCK


def test_hardened_live_prerequisites_do_not_unlock_live_orders() -> None:
    # Given: every live-readiness prerequisite represented in local config.
    settings = RuntimeSettings(
        engine=EngineSettings(live_trading=True, live_trading_confirmed=True),
        exchange=ExchangeSettings(
            name="bybit",
            trading_mode=TradingMode.FUTURES,
            margin_mode=MarginMode.ISOLATED,
            testnet=False,
            api_key=FIXTURE_API_VALUE,
            api_secret=FIXTURE_API_VALUE,
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
        circuit_breakers=CircuitBreakerSettings(manual_halt_file=".runtime/manual-halt"),
        reconciliation=ReconciliationSettings(
            required=True,
            fixture_path="tests/fixtures/exchange/reconcile_match.json",
        ),
    )

    # When: preflight inspects the live-readiness envelope.
    report = run_preflight(settings=settings, profile_name="local-paper")

    # Then: the hardening checks can pass, but real-money execution remains locked.
    assert report.blocked is True
    assert _status(report, PreflightCode.LIVE_TRADING_OUT_OF_SCOPE) is PreflightStatus.BLOCK
    assert _status(report, PreflightCode.LIVE_EXCHANGE_CREDENTIALS) is PreflightStatus.PASS
    assert _status(report, PreflightCode.LIVE_PERMISSION_HARDENING) is PreflightStatus.PASS
    assert _status(report, PreflightCode.LIVE_RECONCILIATION_HARDENING) is PreflightStatus.PASS
    assert _status(report, PreflightCode.LIVE_CIRCUIT_BREAKER_HARDENING) is PreflightStatus.PASS
    assert _status(report, PreflightCode.LIVE_STRATEGY_HARDENING) is PreflightStatus.PASS


def test_invalid_futures_leverage_blocks_readiness() -> None:
    # Given: a futures config with leverage above the milestone readiness ceiling.
    config_path = Path("tests/fixtures/config/futures-liquidation-risk.yaml")
    settings = load_runtime_settings(config_path)

    # When: futures guardrails are checked.
    report = run_preflight(settings=settings, profile_name="bybit-testnet", config_path=config_path)

    # Then: leverage readiness blocks start.
    assert report.blocked is True
    assert _status(report, PreflightCode.FUTURES_LEVERAGE_INVALID) is PreflightStatus.BLOCK


def test_withdrawal_permission_warns_in_dry_run_preflight() -> None:
    # Given: a dry-run config whose exchange key still has withdrawal permission enabled.
    settings = RuntimeSettings(
        exchange=ExchangeSettings(permission_withdrawal=ExchangeApiPermissionState.ENABLED)
    )

    # When: preflight checks exchange API permission readiness.
    report = run_preflight(settings=settings, profile_name="local-paper")

    # Then: the operator sees the unsafe permission without blocking dry-run inspection.
    assert report.blocked is False
    assert _status(report, PreflightCode.EXCHANGE_PERMISSION_AUDIT) is PreflightStatus.WARN


def test_expert_risk_profile_without_confirmation_blocks_preflight() -> None:
    # Given: an expert risk profile without its explicit confirmation flag.
    settings = RuntimeSettings(
        exchange=ExchangeSettings(
            trading_mode=TradingMode.FUTURES,
            margin_mode=MarginMode.ISOLATED,
        ),
        risk=RiskSettings(risk_profile=RiskProfileName.EXPERT, expert_risk_confirmed=False),
    )

    # When: preflight checks risk profile readiness.
    report = run_preflight(settings=settings, profile_name="local-paper")

    # Then: expert mode is blocked until the operator confirms that risk tier.
    assert report.blocked is True
    assert _status(report, PreflightCode.RISK_PROFILE_GUARDRAILS) is PreflightStatus.BLOCK


def test_exchange_without_registry_testnet_support_blocks_readiness(tmp_path: Path) -> None:
    # Given: a candidate exchange whose registry profile has no testnet proof.
    config_path = tmp_path / "bitget.yaml"
    config_path.write_text(
        """exchange:
  name: bitget
  trading_mode: futures
  margin_mode: isolated
  testnet: true
""",
        encoding="utf-8",
    )
    settings = load_runtime_settings(config_path)

    # When: preflight reads exchange readiness from the registry.
    report = run_preflight(settings=settings, profile_name="local-paper", config_path=config_path)

    # Then: testnet support cannot be assumed from docs-only candidate status.
    assert report.blocked is True
    assert _status(report, PreflightCode.EXCHANGE_TESTNET_REQUIRED) is PreflightStatus.BLOCK


def test_disabled_notifier_is_warning_not_blocking() -> None:
    # Given: a safe config with notifications disabled.
    config_path = Path("tests/fixtures/config/preflight-disabled-notifier.yaml")
    settings = load_runtime_settings(config_path)

    # When: notifier readiness is checked.
    report = run_preflight(settings=settings, profile_name="local-paper", config_path=config_path)

    # Then: the operator sees a warning but preflight can pass.
    assert report.blocked is False
    assert _status(report, PreflightCode.NOTIFIER_DISABLED) is PreflightStatus.WARN


def test_frontend_readiness_panel_shows_status_groups() -> None:
    # Given: a passing preflight report.
    config_path = Path("examples/futures-paper.yaml")
    settings = load_runtime_settings(config_path)
    report = run_preflight(settings=settings, profile_name="bybit-testnet", config_path=config_path)

    # When: the settings page renders readiness state.
    html = render_settings_page(settings=settings, readiness=report)

    # Then: pass, warn, and block groups are visible and start remains disabled on blocks.
    assert 'data-testid="readiness-panel"' in html
    assert 'data-testid="readiness-pass"' in html
    assert 'data-testid="readiness-warn"' in html
    assert 'data-testid="readiness-block"' in html
    assert 'data-testid="readiness-start-blocked"' in html
    assert "PREFLIGHT_PASSED" in html


def _status(report: PreflightReport, code: PreflightCode) -> PreflightStatus:
    return next(check.status for check in report.checks if check.code is code)
