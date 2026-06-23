from __future__ import annotations

from nfi_engine.config import Locale
from nfi_engine.config.models import RuntimeSettings, UiSettings
from nfi_engine.ui.assets_data_lifecycle import DATA_LIFECYCLE_SCRIPT
from nfi_engine.ui.pages import render_logs_page, render_settings_page


def test_settings_page_renders_data_lifecycle_controls_without_external_assets() -> None:
    # Given: local operator settings.
    settings = RuntimeSettings()

    # When: the settings page is rendered.
    html = render_settings_page(settings=settings)

    # Then: lifecycle controls are visible and stay local-first.
    assert 'data-testid="settings-data-lifecycle-panel"' in html
    assert 'data-testid="data-lifecycle-footprint-state"' in html
    assert 'data-testid="data-lifecycle-export-state"' in html
    assert 'data-testid="data-lifecycle-prune-state"' in html
    assert 'data-testid="data-lifecycle-retention-days"' in html
    assert 'data-testid="data-lifecycle-preview-token"' in html
    assert 'data-testid="data-lifecycle-inspect-button"' in html
    assert 'data-testid="data-lifecycle-export-button"' in html
    assert 'data-testid="data-lifecycle-dry-run-button"' in html
    assert 'data-testid="data-lifecycle-apply-button"' in html
    assert "https://" not in html
    assert "localStorage" not in html
    assert "sessionStorage" not in html


def test_data_lifecycle_script_uses_csrf_and_no_browser_storage() -> None:
    # Given/When: the settings lifecycle browser script is rendered inline.
    script = DATA_LIFECYCLE_SCRIPT

    # Then: it calls local endpoints through CSRF without browser storage.
    assert "/api/v1/data-lifecycle/footprint" in script
    assert "/api/v1/data-lifecycle/export" in script
    assert "/api/v1/data-lifecycle/prune" in script
    assert "DELETE_GENERATED_LOCAL_ARTIFACTS" in script
    assert "x-nfi-csrf-token" in script
    assert "localStorage" not in script
    assert "sessionStorage" not in script
    assert "https://" not in script


def test_read_only_settings_page_disables_data_lifecycle_apply() -> None:
    # Given: read-only operator settings.
    settings = RuntimeSettings(ui=UiSettings(read_only=True))

    # When: the settings page is rendered.
    html = render_settings_page(settings=settings)

    # Then: mutation controls are visibly locked while inspect/export remain available.
    assert 'data-testid="data-lifecycle-inspect-button"' in html
    assert 'data-testid="data-lifecycle-export-button"' in html
    assert 'data-testid="data-lifecycle-dry-run-button" disabled' in html
    assert 'data-testid="data-lifecycle-apply-button" disabled' in html


def test_settings_data_lifecycle_panel_localizes_korean_and_greek_labels() -> None:
    # Given: operators using Korean and Greek on the local settings page.
    korean = RuntimeSettings(ui=UiSettings(locale=Locale.KO))
    greek = RuntimeSettings(ui=UiSettings(locale=Locale.EL))

    # When: the data lifecycle panel is rendered through the real settings page.
    korean_html = render_settings_page(settings=korean)
    greek_html = render_settings_page(settings=greek)

    # Then: the final Settings panel does not leak its previous English labels.
    assert "로컬 데이터 관리" in korean_html
    assert "보관 일수" in korean_html
    assert "정리 미리보기 실행" in korean_html
    assert "Τοπική διαχείριση δεδομένων" in greek_html
    assert "Ημέρες διατήρησης" in greek_html
    assert "Προεπισκόπηση καθαρισμού" in greek_html
    assert "Local data lifecycle" not in korean_html
    assert "Local data lifecycle" not in greek_html
    assert "Dry run cleanup" not in korean_html
    assert "Dry run cleanup" not in greek_html


def test_logs_page_support_report_link_stays_on_existing_zip_endpoint() -> None:
    # Given: the logs page support workflow.
    settings = RuntimeSettings()

    # When: the logs page is rendered.
    html = render_logs_page(settings=settings, logs=())

    # Then: the existing redacted support archive endpoint remains visible.
    assert 'data-testid="export-support-report"' in html
    assert "/api/v1/reports/support-bundle.zip" in html
