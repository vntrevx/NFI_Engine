from __future__ import annotations

from nfi_engine.config.models import RuntimeSettings, UiSettings
from nfi_engine.ui.pages import render_settings_page


def test_settings_page_renders_schema_driven_safe_controls() -> None:
    settings = RuntimeSettings()

    html = render_settings_page(settings=settings)

    assert 'data-testid="settings-root"' in html
    assert 'data-testid="settings-form"' in html
    assert 'data-testid="setup-form"' in html
    assert 'data-testid="settings-edit-drawer"' in html
    assert 'data-testid="exchange-registry-drawer"' in html
    assert 'data-testid="settings-safety-drawer"' in html
    assert 'data-testid="settings-risk-limit-controls"' in html
    assert 'data-testid="exchange-registry-panel"' in html
    assert 'data-testid="exchange-registry-count">' in html
    assert 'data-testid="exchange-option-bybit"' in html
    assert 'data-testid="exchange-option-binance"' in html
    assert 'data-exchange-pick="bybit"' in html
    assert "official needs: api_key, api_secret, passphrase" in html
    assert "official needs: account_address, api_wallet_signer" in html
    assert 'data-exchange-select="true"' in html
    assert 'name="intent"' in html
    assert 'name="risk.risk_profile"' in html
    assert 'form="settings-form"' in html
    assert 'name="permission_withdrawal"' in html
    assert 'name="api_key" type="password"' in html
    assert 'name="api_secret" type="password"' in html
    assert 'data-testid="setup-step-extra-credentials"' in html
    assert 'name="passphrase" type="password"' in html
    assert 'name="memo" type="password"' in html
    assert 'name="operator_id" type="password"' in html
    assert 'name="account_address" type="password"' in html
    assert 'name="api_wallet_signer" type="password"' in html
    assert 'name="risk.stake_usdt"' in html
    assert 'name="risk.max_open_trades"' in html
    assert 'type="number"' in html
    assert 'data-runtime-safe="true"' in html
    assert 'data-testid="validation-state"' in html
    assert 'data-testid="audit-log"' in html
    assert 'data-testid="live-trading-locked"' in html
    assert 'data-testid="runtime-control-state"' in html
    assert 'data-testid="runtime-health-state"' in html
    assert 'data-testid="pause-button"' in html
    assert 'data-testid="resume-button"' in html
    assert 'data-command="start"' in html
    assert 'data-command="pause"' in html
    assert 'data-command="resume"' in html
    assert 'data-command="stop"' in html
    assert "raw yaml" not in html.lower()
    assert "exchange.api_secret" not in html
    assert "api.auth_token" not in html
    assert 'value="real-secret"' not in html
    assert "https://" not in html
    assert "cdn" not in html.lower()


def test_settings_page_keeps_advanced_fields_discoverable_without_sensitive_values() -> None:
    settings = RuntimeSettings()

    html = render_settings_page(settings=settings)

    assert 'name="notifications.max_attempts"' in html
    assert 'name="backtest.fee_rate"' in html
    assert "exchange.api_key" not in html
    assert "exchange.api_secret" not in html


def test_settings_page_renders_simple_mode_before_advanced_controls() -> None:
    settings = RuntimeSettings()

    html = render_settings_page(settings=settings)

    simple_start = html.index('data-testid="simple-settings"')
    setup_start = html.index('data-testid="setup-preview-panel"')
    advanced_start = html.index('data-testid="advanced-settings"')
    setup_html = html[setup_start:simple_start]
    simple_html = html[simple_start:advanced_start]
    assert setup_start < simple_start
    assert simple_start < advanced_start
    assert 'name="intent"' in setup_html
    assert 'name="risk_profile"' not in setup_html
    assert 'name="permission_withdrawal"' in setup_html
    assert 'name="api_key" type="password"' in setup_html
    assert 'name="api_secret" type="password"' in setup_html
    assert 'name="exchange.name"' in simple_html
    assert '<option value="bybit">Bybit - verified - spot/futures</option>' in simple_html
    assert '<option value="binance">Binance - verified - spot/futures</option>' in simple_html
    assert 'name="exchange.trading_mode"' in simple_html
    assert 'name="ui.locale"' in simple_html
    assert '<option value="en" selected>English</option>' in simple_html
    assert '<option value="ko">한국어</option>' in simple_html
    assert '<option value="el">Ελληνικά</option>' in simple_html
    assert 'name="risk.stake_usdt"' in simple_html
    assert 'name="risk.max_open_trades"' in simple_html
    assert 'name="risk.risk_profile"' not in simple_html


def test_settings_page_renders_first_run_wizard_in_operator_order() -> None:
    settings = RuntimeSettings()

    html = render_settings_page(settings=settings)

    markers = (
        'data-testid="setup-step-exchange"',
        'data-testid="setup-step-api-key"',
        'data-testid="setup-step-api-secret"',
        'data-testid="setup-step-extra-credentials"',
        'data-testid="setup-step-permission-audit"',
        'data-testid="setup-step-leverage"',
        'data-testid="setup-step-wallet-balance"',
        'data-testid="setup-step-allocated-amount"',
        'data-testid="setup-step-market-mode"',
        'data-testid="setup-step-intent"',
    )
    positions = tuple(html.index(marker) for marker in markers)
    assert positions == tuple(sorted(positions))
    assert 'data-testid="wallet-fetch-button"' in html
    assert 'name="allocated_amount_usdt"' in html
    assert 'name="permission_withdrawal"' in html
    assert 'data-testid="setup-step-risk-profile"' not in html
    assert 'name="risk_profile"' not in html
    assert 'data-testid="settings-risk-profile-control"' in html
    assert 'name="risk.risk_profile"' in html
    assert 'data-testid="setup-recommended-leverage">3x<' in html
    assert '<option value="paper" selected>Dry-run</option>' in html
    assert (
        '<details class="setup-permission-drawer" data-testid="setup-step-permission-audit">'
        in html
    )
    assert "wallet seed" not in html.lower()
    assert "private key" not in html.lower()


def test_settings_page_renders_developer_update_states_without_network_action() -> None:
    settings = RuntimeSettings()

    html = render_settings_page(settings=settings)

    assert 'data-testid="settings-update-panel"' in html
    assert 'data-testid="update-preview-state"' in html
    assert 'data-testid="update-apply-state"' in html
    assert 'data-testid="update-rollback-state"' in html
    assert 'data-testid="update-preview-button"' in html
    assert 'data-testid="update-apply-button"' in html
    assert 'data-testid="update-rollback-button"' in html
    assert 'data-testid="update-backup-reference"' in html
    assert 'data-testid="update-acknowledge-unverified"' in html
    assert "engine + strategy" in html
    assert "https://" not in html


def test_read_only_settings_page_locks_mutating_controls_without_token_storage() -> None:
    settings = RuntimeSettings(ui=UiSettings(read_only=True))

    html = render_settings_page(settings=settings)

    assert 'data-testid="readonly-reason"' in html
    assert 'data-testid="save-draft-button" disabled' in html
    assert 'data-testid="apply-button" disabled' in html
    assert 'data-testid="restore-button" disabled' in html
    assert 'data-testid="start-button" disabled' in html
    assert 'data-testid="pause-button" disabled' in html
    assert 'data-testid="resume-button" disabled' in html
    assert 'data-testid="stop-button" disabled' in html
    assert "Read-only mode blocks changes" in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html
