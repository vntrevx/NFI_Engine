from __future__ import annotations

from typing import Final

from nfi_engine.config import Locale, RuntimeSettings, UiSettings
from nfi_engine.ui.pages import render_settings_page

FORBIDDEN_SETUP_TERMS: Final = (
    "wallet seed",
    "seed phrase",
    "private key",
    "mnemonic",
    "withdrawal key",
    "api auth token",
    "login token",
    "operator token",
    "지갑 시드",
    "개인 키",
    "개인키",
    "니모닉",
    "출금 키",
    "로그인 토큰",
    "운영자 토큰",
    "φράση seed",
    "ιδιωτικό κλειδί",
    "κλειδί ανάληψης",
    "token σύνδεσης",
    "token χειριστή",
)


def test_settings_setup_labels_exchange_api_credentials_without_wallet_or_login_terms() -> None:
    cases = (
        (Locale.EN, ("Exchange API key", "Exchange API secret")),
        (Locale.KO, ("거래소 API 키", "거래소 API 시크릿")),
        (Locale.EL, ("Κλειδί API ανταλλακτηρίου", "Μυστικό API ανταλλακτηρίου")),
    )

    for locale, expected_labels in cases:
        # Given: the Settings page is rendered in an operator locale.
        settings = RuntimeSettings(ui=UiSettings(locale=locale))

        # When: the first-run setup panel is isolated from the broader page.
        html = render_settings_page(settings=settings)
        setup_html = html.split('data-testid="setup-preview-panel"', 1)[1].split(
            'data-testid="settings-form"',
            1,
        )[0]
        normalized_setup = setup_html.casefold()

        # Then: credentials are exchange API fields, not wallet keys or login tokens.
        for label in expected_labels:
            assert label in setup_html
        assert 'name="api_key" type="password"' in setup_html
        assert 'name="api_secret" type="password"' in setup_html
        for forbidden_term in FORBIDDEN_SETUP_TERMS:
            assert forbidden_term.casefold() not in normalized_setup
