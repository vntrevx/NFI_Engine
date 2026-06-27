from __future__ import annotations

import pytest

from nfi_engine.config import Locale
from nfi_engine.config.models import RuntimeSettings, UiSettings
from nfi_engine.ui.i18n import CATALOGS, localize, supported_locales
from nfi_engine.ui.i18n_keys import MessageKey
from nfi_engine.ui.pages import render_home_page, render_logs_page, render_settings_page


def test_i18n_catalog_supports_required_locales_with_complete_frontend_keys() -> None:
    # Given: all M2 frontend locales.
    locales = supported_locales()

    # When: each catalog is compared with the typed message-key set.
    missing_by_locale = {
        locale: sorted(key.value for key in set(MessageKey) - set(CATALOGS[locale]))
        for locale in locales
    }

    # Then: locale lookup is typed and complete without changing machine codes.
    assert locales == (Locale.EN, Locale.KO, Locale.EL)
    assert missing_by_locale == {Locale.EN: [], Locale.KO: [], Locale.EL: []}
    assert localize(Locale.KO, MessageKey.HOME_SUBTITLE) == "운영자 커맨드 센터"
    assert localize(Locale.EL, MessageKey.LOGS_TITLE) == "Πρόσφατα logs και report bundle"
    assert localize(Locale.EL, MessageKey.SETTINGS_TITLE) == "Τοπικές ρυθμίσεις χειριστή"
    assert localize(Locale.KO, MessageKey.MACHINE_CODE_SAMPLE) == "CONFIG_VALIDATION_ERROR"
    assert localize(Locale.KO, MessageKey.CHART_REFRESH_FAILED) == "스냅샷 새로고침 실패."


@pytest.mark.parametrize("locale", [Locale.EN, Locale.KO, Locale.EL])
def test_pages_render_dynamic_html_lang_for_each_locale(locale: Locale) -> None:
    # Given: runtime settings with an explicit frontend locale.
    settings = RuntimeSettings(ui=UiSettings(locale=locale))

    # When: all server-rendered pages are rendered.
    home = render_home_page(settings=settings, logs=())
    settings_page = render_settings_page(settings=settings)
    logs = render_logs_page(settings=settings, logs=())

    # Then: each page uses the configured language while preserving test contracts.
    expected_lang = f'<html lang="{locale.value}">'
    assert expected_lang in home
    assert expected_lang in settings_page
    assert expected_lang in logs
    assert 'data-testid="home-root"' in home
    assert 'data-testid="settings-root"' in settings_page
    assert 'data-testid="logs-root"' in logs


def test_runtime_settings_reject_unknown_locale() -> None:
    # Given: an unsupported locale value.
    raw_settings = {"ui": {"locale": "jp"}}

    # When / Then: config parsing rejects it at the boundary.
    with pytest.raises(ValueError, match=r"ui\.locale"):
        RuntimeSettings.model_validate(raw_settings)


def test_settings_operator_select_options_are_localized() -> None:
    # Given: Korean and Greek operator Settings pages.
    korean = render_settings_page(settings=RuntimeSettings(ui=UiSettings(locale=Locale.KO)))
    greek = render_settings_page(settings=RuntimeSettings(ui=UiSettings(locale=Locale.EL)))

    # When / Then: Settings field options use the i18n catalog, not title-cased ids.
    assert '<option value="futures">선물</option>' in korean
    assert '<option value="balanced" selected>균형</option>' in korean
    assert '<option value="futures">Συμβόλαια</option>' in greek
    assert '<option value="balanced" selected>Ισορροπημένο</option>' in greek
    assert "Bybit - 검증됨 - 현물/선물" in korean
    assert "Binance - 검증됨 - 현물/선물" in korean
    assert "Bybit - επαληθευμένο - spot/συμβόλαια" in greek
    assert '<option value="futures">Futures</option>' not in korean
    assert '<option value="balanced" selected>Balanced</option>' not in greek


def test_greek_catalog_localizes_visible_operator_labels() -> None:
    # Given: visible operator labels that are not machine codes.
    visible_labels = {
        MessageKey.COMMON_BLOCK: "Αποκλεισμός",
        MessageKey.COMMON_PASSED: "Πέρασε",
        MessageKey.COMMON_WARN: "Προσοχή",
        MessageKey.SAVE_DRAFT: "Αποθήκευση προσχεδίου",
        MessageKey.SETTINGS_RUNTIME_SAFE: "Ασφαλές runtime",
        MessageKey.SETTINGS_RUNTIME_SAFE_TITLE: "Ασφαλείς ρυθμίσεις runtime",
        MessageKey.SETTINGS_UPDATE_ROLLBACK: "Επαναφορά",
        MessageKey.SETTINGS_UPDATE_TITLE: "Ενημέρωση προγραμματιστή",
        MessageKey.HOME_PAIRLIST: "Λίστα ζευγών",
        MessageKey.PAIRLIST_BLACKLIST: "Λίστα αποκλεισμού",
        MessageKey.PAIRLIST_BLACKLIST_ARIA: "λίστα αποκλεισμού ζευγών",
        MessageKey.PAIRLIST_PREVIEW_EMPTY: "Δεν υπάρχει προεπισκόπηση λίστας ζευγών",
        MessageKey.PAIRLIST_TITLE: "Λίστα ζευγών",
        MessageKey.SETUP_FETCH_WALLET: "Φόρτωση υπολοίπου πορτοφολιού",
        MessageKey.SETUP_WALLET_NOT_FETCHED: (
            "\u03a4\u03bf υπόλοιπο πορτοφολιού δεν έχει φορτωθεί ακόμη."
        ),
    }

    # When / Then: Greek user-facing copy is translated while machine terms can stay stable.
    for key, expected in visible_labels.items():
        assert localize(Locale.EL, key) == expected
