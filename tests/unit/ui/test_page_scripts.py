from __future__ import annotations

from pathlib import Path

from nfi_engine.api.models import initial_log_entries
from nfi_engine.config.models import RuntimeSettings
from nfi_engine.ui.assets import STYLE
from nfi_engine.ui.assets_exchange_picker import EXCHANGE_PICKER_SCRIPT
from nfi_engine.ui.assets_runtime_control import RUNTIME_CONTROL_SCRIPT
from nfi_engine.ui.assets_settings import SETTINGS_SCRIPT
from nfi_engine.ui.pages import render_home_page, render_logs_page, render_settings_page

FRONTEND_SRC = Path("frontend/src")


def _react_shell(html: str) -> bool:
    return 'id="nfi-react-root"' in html


def _frontend_text(*parts: str) -> str:
    return (FRONTEND_SRC.joinpath(*parts)).read_text(encoding="utf-8")


def test_settings_locale_apply_contract_uses_reload_without_browser_storage() -> None:
    # Given: a settings page with an editable runtime locale field.
    html = render_settings_page(settings=RuntimeSettings())

    if _react_shell(html):
        api_source = _frontend_text("api.ts")
        settings_source = _frontend_text("components", "SettingsPanel.tsx")
        assert 'name="ui.locale"' in settings_source
        assert 'testId="apply-button"' in settings_source
        assert "/api/v1/config/apply" in api_source
        assert "document.documentElement.lang = locale" in settings_source
        assert "localStorage" not in api_source
        assert "sessionStorage" not in api_source
        return

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

    if _react_shell(html):
        api_source = _frontend_text("api.ts")
        settings_source = _frontend_text("components", "SettingsPanel.tsx")
        assert 'testId="wallet-fetch-button"' in settings_source
        assert 'data-testid="wallet-balance-state"' in settings_source
        assert "/api/v1/wallet/balance/fetch" in api_source
        assert 'method: "POST"' in api_source
        assert "localStorage" not in api_source
        assert "sessionStorage" not in api_source
        return

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

    if _react_shell(html):
        settings_source = _frontend_text("components", "SettingsPanel.tsx")
        assert "EXCHANGES" in settings_source
        assert "bybit" in settings_source
        assert 'name="exchange"' in settings_source
        assert "localStorage" not in settings_source
        assert "sessionStorage" not in settings_source
        return

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

    if _react_shell(html):
        logs_source = _frontend_text("components", "LogsPanel.tsx")
        css_source = _frontend_text("styles.css")
        assert 'className="machine-code"' in logs_source
        assert ".machine-code" in css_source
        assert "CONFIG_VALIDATION_ERROR" in logs_source
        return

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

    if _react_shell(html):
        api_source = _frontend_text("api.ts")
        home_source = _frontend_text("components", "HomePanel.tsx")
        assert "/api/v1/runtime/control" in api_source
        assert "/api/v1/runtime/health" in api_source
        assert 'meta name="nfi-csrf-token"' in html
        assert 'command="start"' in home_source
        assert 'command="pause"' in home_source
        assert 'command="resume"' in home_source
        assert 'command="stop"' in home_source
        assert "localStorage" not in api_source
        assert "sessionStorage" not in api_source
        return

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
