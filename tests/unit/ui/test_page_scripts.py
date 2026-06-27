from __future__ import annotations

from nfi_engine.api.models import initial_log_entries
from nfi_engine.config.models import RuntimeSettings
from nfi_engine.ui.assets import STYLE
from nfi_engine.ui.assets_exchange_picker import EXCHANGE_PICKER_SCRIPT
from nfi_engine.ui.assets_runtime_control import RUNTIME_CONTROL_SCRIPT
from nfi_engine.ui.assets_settings import SETTINGS_SCRIPT
from nfi_engine.ui.pages import render_home_page, render_logs_page, render_settings_page


def test_settings_locale_apply_contract_uses_reload_without_browser_storage() -> None:
    # Given: a settings page with an editable runtime locale field.
    html = render_settings_page(settings=RuntimeSettings())

    # Then: the page has the operator control and the local script can apply it safely.
    assert 'name="ui.locale"' in html
    assert 'data-testid="apply-button"' in html
    assert "/api/v1/config/apply" in SETTINGS_SCRIPT
    assert "window.location.reload()" in SETTINGS_SCRIPT
    assert "localStorage" not in SETTINGS_SCRIPT
    assert "sessionStorage" not in SETTINGS_SCRIPT


def test_settings_wallet_fetch_contract_uses_post_without_browser_storage() -> None:
    # Given: a settings page with the wallet fetch affordance.
    html = render_settings_page(settings=RuntimeSettings())

    # Then: the browser script posts to the wallet endpoint and keeps secrets out of storage.
    assert 'data-testid="wallet-fetch-button"' in html
    assert 'data-testid="wallet-balance-state"' in html
    assert "/api/v1/wallet/balance/fetch" in SETTINGS_SCRIPT
    assert "method: 'POST'" in SETTINGS_SCRIPT
    assert "setup.wallet_loading" in SETTINGS_SCRIPT
    assert "setup.wallet_fetched" in SETTINGS_SCRIPT
    assert "localStorage" not in SETTINGS_SCRIPT
    assert "sessionStorage" not in SETTINGS_SCRIPT


def test_settings_exchange_registry_click_contract_stays_local_to_form_values() -> None:
    # Given: Settings renders the registry picker and setup form selects.
    html = render_settings_page(settings=RuntimeSettings())

    # Then: the client script syncs visible select values without browser storage.
    assert 'data-testid="exchange-registry-panel"' in html
    assert 'data-exchange-pick="bybit"' in html
    assert 'name="exchange"' in html
    assert 'name="exchange.name"' in html
    assert "setExchangeSelectValue" in html
    assert "data-exchange-pick" in EXCHANGE_PICKER_SCRIPT
    assert "setExchangeSelectValue" in EXCHANGE_PICKER_SCRIPT
    assert "'[name=\"exchange\"]'" in EXCHANGE_PICKER_SCRIPT
    assert "'[name=\"exchange.name\"]'" in EXCHANGE_PICKER_SCRIPT
    assert "localStorage" not in SETTINGS_SCRIPT
    assert "sessionStorage" not in SETTINGS_SCRIPT
    assert "localStorage" not in EXCHANGE_PICKER_SCRIPT
    assert "sessionStorage" not in EXCHANGE_PICKER_SCRIPT


def test_logs_page_preserves_machine_code_visual_contract() -> None:
    # Given: seeded logs with stable machine-code identifiers.
    html = render_logs_page(settings=RuntimeSettings(), logs=initial_log_entries())

    # Then: the rendered table and stylesheet preserve scan-friendly machine tokens.
    assert 'class="log-time" title="' in html
    assert 'class="machine-code"' in html
    assert ".log-time" in STYLE
    assert ".machine-code" in STYLE
    assert "white-space: nowrap;" in STYLE
    assert "word-break: keep-all;" in STYLE


def test_runtime_control_contract_posts_commands_and_refreshes_health() -> None:
    csrf_value = "fixture"
    html = render_home_page(settings=RuntimeSettings(), logs=(), csrf_token=csrf_value)

    assert "/api/v1/runtime/control" in html
    assert "/api/v1/runtime/health" in html
    assert 'meta name="nfi-csrf-token"' in html
    assert 'data-command="start"' in html
    assert 'data-command="pause"' in html
    assert 'data-command="resume"' in html
    assert 'data-command="stop"' in html
    assert "/api/v1/runtime/control" in RUNTIME_CONTROL_SCRIPT
    assert "/api/v1/runtime/health" in RUNTIME_CONTROL_SCRIPT
    assert "settings.runtime_control_loading" in RUNTIME_CONTROL_SCRIPT
    assert "settings.runtime_control_blocked" in RUNTIME_CONTROL_SCRIPT
    assert "localStorage" not in RUNTIME_CONTROL_SCRIPT
    assert "sessionStorage" not in RUNTIME_CONTROL_SCRIPT
