from __future__ import annotations

from nfi_engine.config import Locale
from nfi_engine.config.models import RuntimeSettings, UiSettings
from nfi_engine.ui.assets_settings import SETTINGS_SCRIPT
from nfi_engine.ui.pages import render_settings_page
from nfi_engine.ui.settings_update import render_settings_update_panel


def test_settings_update_panel_renders_local_proof_controls() -> None:
    # Given: default local runtime settings.
    settings = RuntimeSettings()

    # When: the update panel is rendered.
    html = render_settings_update_panel(settings=settings)

    # Then: backup proof and unverified acknowledgement controls are visible.
    assert 'data-testid="settings-update-panel"' in html
    assert 'data-testid="update-preview-button"' in html
    assert 'data-testid="update-apply-button"' in html
    assert 'data-testid="update-rollback-button"' in html
    assert 'data-testid="update-backup-reference"' in html
    assert 'data-testid="update-acknowledge-unverified"' in html
    assert 'data-testid="update-allow-dirty-worktree"' in html
    assert 'data-testid="update-source"' in html
    assert "engine + strategy" in html
    assert "disabled" not in html


def test_settings_page_and_script_use_local_update_endpoints_without_browser_storage() -> None:
    # Given: the settings page and script assets.
    html = render_settings_page(settings=RuntimeSettings())

    # When / Then: local update proof routes are wired without browser storage or external assets.
    assert "/api/v1/update/preview" in SETTINGS_SCRIPT
    assert "/api/v1/update/apply" in SETTINGS_SCRIPT
    assert "/api/v1/update/rollback" in SETTINGS_SCRIPT
    assert "x-nfi-csrf-token" in SETTINGS_SCRIPT
    assert "allow_dirty_worktree" in SETTINGS_SCRIPT
    assert "update_source" in SETTINGS_SCRIPT
    assert "local_proof" in SETTINGS_SCRIPT
    assert "localStorage" not in SETTINGS_SCRIPT
    assert "sessionStorage" not in SETTINGS_SCRIPT
    assert "https://" not in html
    assert "sessionStorage" not in html


def test_settings_update_panel_localizes_new_proof_labels() -> None:
    # Given: Korean runtime settings.
    settings = RuntimeSettings(ui=UiSettings(locale=Locale.KO))

    # When: the update proof panel is rendered.
    html = render_settings_update_panel(settings=settings)

    # Then: the new proof controls use localized labels.
    assert "백업 참조" in html
    assert "검증되지 않은 출처 확인" in html
    assert "변경된 작업트리 허용" in html
