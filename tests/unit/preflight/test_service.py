from __future__ import annotations

from pathlib import Path

from nfi_engine.config import load_runtime_settings
from nfi_engine.preflight import PreflightCode, PreflightReport, PreflightStatus, run_preflight
from nfi_engine.ui.pages import render_settings_page


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


def test_invalid_futures_leverage_blocks_readiness() -> None:
    # Given: a futures config with leverage above the milestone readiness ceiling.
    config_path = Path("tests/fixtures/config/futures-liquidation-risk.yaml")
    settings = load_runtime_settings(config_path)

    # When: futures guardrails are checked.
    report = run_preflight(settings=settings, profile_name="bybit-testnet", config_path=config_path)

    # Then: leverage readiness blocks start.
    assert report.blocked is True
    assert _status(report, PreflightCode.FUTURES_LEVERAGE_INVALID) is PreflightStatus.BLOCK


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
