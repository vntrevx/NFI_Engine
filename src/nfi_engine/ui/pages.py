from __future__ import annotations

from typing import TYPE_CHECKING

from nfi_engine.api.models import LogEntryResponse
from nfi_engine.config import RuntimeSettings
from nfi_engine.ui.assets_dashboard import DASHBOARD_SCRIPT, DASHBOARD_STYLE
from nfi_engine.ui.assets_data_lifecycle import DATA_LIFECYCLE_SCRIPT
from nfi_engine.ui.assets_exchange_picker import EXCHANGE_PICKER_SCRIPT
from nfi_engine.ui.assets_login import LOGIN_SCRIPT
from nfi_engine.ui.assets_logs import LOGS_SCRIPT
from nfi_engine.ui.assets_pairlist import PAIRLIST_SCRIPT
from nfi_engine.ui.assets_runtime_control import RUNTIME_CONTROL_SCRIPT
from nfi_engine.ui.assets_settings import SETTINGS_SCRIPT
from nfi_engine.ui.document import render_document, render_nav
from nfi_engine.ui.home import render_home_body
from nfi_engine.ui.home_context import HomeRuntimeContext
from nfi_engine.ui.i18n import localize, render_i18n_script
from nfi_engine.ui.i18n_keys import MessageKey
from nfi_engine.ui.login_page import render_login_body
from nfi_engine.ui.logs_page import render_logs_body
from nfi_engine.ui.react_app import react_app_available, render_react_app_page
from nfi_engine.ui.settings_page import render_settings_body

if TYPE_CHECKING:
    from nfi_engine.preflight.models import PreflightReport


def render_home_page(
    *,
    settings: RuntimeSettings,
    logs: tuple[LogEntryResponse, ...],
    runtime: HomeRuntimeContext | None = None,
    csrf_token: str = "",
) -> str:
    locale = settings.ui.locale
    home_body = render_home_body(
        settings=settings,
        logs=logs,
        runtime=runtime or HomeRuntimeContext(),
        nav=render_nav(active="home", locale=locale),
    )
    if react_app_available():
        return render_react_app_page(
            title=localize(settings.ui.locale, MessageKey.HOME_DOCUMENT_TITLE),
            locale=locale,
            csrf_token=csrf_token,
            page="home",
            fallback_body=home_body,
        )
    return render_document(
        title=localize(settings.ui.locale, MessageKey.HOME_DOCUMENT_TITLE),
        locale=locale,
        csrf_token=csrf_token,
        extra_style=DASHBOARD_STYLE,
        body=home_body
        + render_i18n_script(settings.ui.locale)
        + RUNTIME_CONTROL_SCRIPT
        + DASHBOARD_SCRIPT,
    )


def render_settings_page(
    *,
    settings: RuntimeSettings,
    readiness: PreflightReport | None = None,
    csrf_token: str = "",
) -> str:
    locale = settings.ui.locale
    settings_body = render_settings_body(
        settings=settings,
        readiness=readiness,
        nav=render_nav(active="settings", locale=locale),
    )
    if react_app_available():
        return render_react_app_page(
            title=localize(settings.ui.locale, MessageKey.SETTINGS_DOCUMENT_TITLE),
            locale=locale,
            csrf_token=csrf_token,
            page="settings",
            fallback_body=settings_body,
        )
    return render_document(
        title=localize(settings.ui.locale, MessageKey.SETTINGS_DOCUMENT_TITLE),
        locale=locale,
        csrf_token=csrf_token,
        body=settings_body
        + render_i18n_script(settings.ui.locale)
        + SETTINGS_SCRIPT
        + EXCHANGE_PICKER_SCRIPT
        + DATA_LIFECYCLE_SCRIPT
        + RUNTIME_CONTROL_SCRIPT
        + PAIRLIST_SCRIPT,
    )


def render_logs_page(
    *,
    settings: RuntimeSettings,
    logs: tuple[LogEntryResponse, ...],
    csrf_token: str = "",
) -> str:
    locale = settings.ui.locale
    logs_body = render_logs_body(
        settings=settings,
        logs=logs,
        nav=render_nav(active="logs", locale=locale),
    )
    if react_app_available():
        return render_react_app_page(
            title=localize(settings.ui.locale, MessageKey.LOGS_DOCUMENT_TITLE),
            locale=locale,
            csrf_token=csrf_token,
            page="logs",
            fallback_body=logs_body,
        )
    return render_document(
        title=localize(settings.ui.locale, MessageKey.LOGS_DOCUMENT_TITLE),
        locale=locale,
        csrf_token=csrf_token,
        body=logs_body + render_i18n_script(settings.ui.locale) + LOGS_SCRIPT,
    )


def render_login_page(*, settings: RuntimeSettings) -> str:
    return render_document(
        title=localize(settings.ui.locale, MessageKey.LOGIN_DOCUMENT_TITLE),
        locale=settings.ui.locale,
        body=render_login_body(settings=settings)
        + render_i18n_script(settings.ui.locale)
        + LOGIN_SCRIPT,
    )
