from __future__ import annotations

# ruff: noqa: RUF001
from typing import TYPE_CHECKING

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.config import Locale
from nfi_engine.config.models import ApiSettings, RuntimeSettings, UiSettings
from nfi_engine.dashboard.store import StaticDashboardReadStore

if TYPE_CHECKING:
    from fastapi import FastAPI

LOCAL_BEARER = "local-test-bearer"


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("locale", "expected"),
    [
        (
            Locale.EN,
            (
                "Bot state",
                "Setup Doctor",
                "Simple Mode",
                "Exchange name",
                "Validate",
                "Recent events",
                "Snapshot refresh failed.",
                "Support bundle",
                "Runtime-safe settings",
                "Safety gates",
                "No pairlist preview",
                "Severity",
                "Error lookup",
                '"settings.runtime_applied":"runtime applied"',
                "Local operator login",
                "First-run setup",
                "Preview setup",
                "Dry-run",
                '"settings.fix_settings":"Fix settings"',
                "Pause",
                "Resume",
                '"settings.runtime_control_state":"Runtime control state"',
                '"settings.runtime_control_loading":"Sending runtime command..."',
                '"settings.runtime_control_blocked":"Runtime command blocked"',
            ),
        ),
        (
            Locale.KO,
            (
                "봇 상태",
                "설정 진단",
                "간편 모드",
                "거래소 이름",
                "검증",
                "최근 이벤트",
                "스냅샷 새로고침 실패.",
                "지원 번들",
                "런타임 안전 설정",
                "안전 게이트",
                "페어리스트 미리보기 없음",
                "심각도",
                "에러 조회",
                '"settings.runtime_applied":"런타임 적용됨"',
                "로컬 운영자 로그인",
                "첫 실행 설정",
                "설정 미리보기",
                "드라이런",
                '"settings.fix_settings":"설정을 수정하세요"',
                "일시 중지",
                "재개",
                '"settings.runtime_control_state":"런타임 제어 상태"',
                '"settings.runtime_control_loading":"런타임 명령 전송 중..."',
                '"settings.runtime_control_blocked":"런타임 명령이 차단됨"',
            ),
        ),
        (
            Locale.EL,
            (
                "Κατάσταση bot",
                "Έλεγχος ρύθμισης",
                "Απλή λειτουργία",
                "Όνομα exchange",
                "Έλεγχος",
                "Πρόσφατα γεγονότα",
                "Η ανανέωση snapshot απέτυχε.",
                "Bundle υποστήριξης",
                "Ασφαλείς ρυθμίσεις runtime",
                "Πύλες ασφάλειας",
                "Δεν υπάρχει προεπισκόπηση λίστας ζευγών",
                "Σοβαρότητα",
                "Αναζήτηση σφάλματος",
                '"settings.runtime_applied":"runtime εφαρμόστηκε"',
                "Σύνδεση τοπικού χειριστή",
                "Ρύθμιση πρώτης εκτέλεσης",
                "Προεπισκόπηση ρύθμισης",
                "Dry-run",
                '"settings.fix_settings":"Διορθώστε τις ρυθμίσεις"',
                "Παύση",
                "Συνέχιση",
                '"settings.runtime_control_state":"Κατάσταση ελέγχου runtime"',
                '"settings.runtime_control_loading":"Αποστολή εντολής runtime..."',
                '"settings.runtime_control_blocked":"Η εντολή runtime αποκλείστηκε"',
            ),
        ),
    ],
)
async def test_home_settings_and_logs_are_localized_without_changing_contracts(
    locale: Locale,
    expected: tuple[str, ...],
) -> None:
    # Given: a local console configured with an explicit frontend locale.
    settings = RuntimeSettings(ui=UiSettings(locale=locale))

    protected_settings = RuntimeSettings(
        ui=UiSettings(locale=locale),
        api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}),
    )

    async with _client(create_app(settings=settings)) as client:
        # When: the operator opens all server-rendered pages.
        home = await client.get("/")
        settings_page = await client.get("/settings")
        logs = await client.get("/logs")
    async with _client(
        create_app(
            settings=protected_settings,
            dashboard_store=StaticDashboardReadStore(),
        ),
    ) as client:
        login = await client.get("/")

    # Then: user-facing copy changes, while contracts and machine codes stay stable.
    expected_lang = f'<html lang="{locale.value}">'
    pages = (home.text, settings_page.text, logs.text)
    assert all(response.status_code == 200 for response in (home, settings_page, logs))
    assert login.status_code == 401
    assert all(expected_lang in page for page in pages)
    assert expected_lang in login.text
    assert expected[0] in home.text
    assert expected[1] in home.text
    assert expected[2] in settings_page.text
    assert expected[3] in settings_page.text
    assert expected[4] in settings_page.text
    assert expected[5] in logs.text
    assert expected[6] in home.text
    assert expected[7] in home.text
    assert expected[8] in settings_page.text
    assert expected[9] in settings_page.text
    assert expected[10] in settings_page.text
    assert expected[11] in logs.text
    assert expected[12] in logs.text
    assert expected[13] in settings_page.text
    assert expected[14] in login.text
    assert expected[15] in settings_page.text
    assert expected[16] in settings_page.text
    assert expected[17] in settings_page.text
    assert expected[18] in settings_page.text
    assert expected[19] in home.text
    assert expected[20] in home.text
    assert expected[21] in settings_page.text
    assert expected[22] in settings_page.text
    assert expected[23] in settings_page.text
    assert "CONFIG_VALIDATION_ERROR" in logs.text
    assert all('data-testid="' in page for page in pages)
    assert 'data-testid="login-form"' in login.text
    all_pages = (*pages, login.text)
    assert not any("navigator.language" in page for page in all_pages)
    assert not any("localStorage" in page or "sessionStorage" in page for page in all_pages)


@pytest.mark.anyio
@pytest.mark.parametrize("locale", [Locale.KO, Locale.EL])
async def test_localized_pages_do_not_leak_obvious_setup_or_login_english(
    locale: Locale,
) -> None:
    settings = RuntimeSettings(ui=UiSettings(locale=locale))
    protected_settings = RuntimeSettings(
        ui=UiSettings(locale=locale),
        api=ApiSettings.model_validate({"auth_token": LOCAL_BEARER}),
    )

    async with _client(create_app(settings=settings)) as client:
        settings_page = await client.get("/settings")
    async with _client(
        create_app(
            settings=protected_settings,
            dashboard_store=StaticDashboardReadStore(),
        ),
    ) as client:
        login = await client.get("/")

    leaked = (
        "Local operator login",
        "Use the local admin account created during install.",
        "Username",
        "Password",
        "Operator token",
        "Paste the token from the generated local runtime env file.",
        "First-run setup",
        "Preview setup",
        "No setup preview",
        "Fix settings",
        "loaded runtime settings",
        "local simulator or paper trading profile",
        "api bind is local",
        "api auth policy passed",
        "live trading is disabled",
        "exchange mode is simulator or testnet",
        "SQLite path is ready",
        "log path is writable",
        "compose named volumes are configured",
        "notifier dry-run path is configured",
        "pair config passed",
        "startup reconciliation is not required",
    )
    combined = settings_page.text + login.text
    assert not any(text in combined for text in leaked)


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
