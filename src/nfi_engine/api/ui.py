from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from nfi_engine.api.models import LogEntryResponse
from nfi_engine.api.security import SecurityContext
from nfi_engine.api.security_store import SecuritySession
from nfi_engine.config import RuntimeSettings
from nfi_engine.dashboard import DashboardReadModels
from nfi_engine.ui import (
    render_home_page,
    render_login_page,
    render_logs_page,
    render_settings_page,
)

if TYPE_CHECKING:
    from nfi_engine.dashboard import DashboardReadStore
    from nfi_engine.preflight.models import PreflightReport

bearer_scheme = HTTPBearer(auto_error=False)
SettingsProvider = Callable[[], RuntimeSettings]


def home_page(
    settings: SettingsProvider,
    logs: tuple[LogEntryResponse, ...],
    readiness: PreflightReport | None = None,
    security: SecurityContext | None = None,
    dashboard_store: DashboardReadStore | None = None,
) -> Callable[[Request, HTTPAuthorizationCredentials | None], Awaitable[HTMLResponse]]:
    async def endpoint(
        request: Request,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Depends(bearer_scheme),
        ] = None,
    ) -> HTMLResponse:
        current_settings = settings()
        login = _login_response_if_unauthorized(
            security=security,
            settings=current_settings,
            request=request,
            credentials=credentials,
        )
        if login is not None:
            return login
        session = _frontend_session(security=security, request=request, credentials=credentials)
        response = HTMLResponse(
            content=render_home_page(
                settings=current_settings,
                logs=logs,
                read_models=await _read_models(dashboard_store),
                readiness=readiness,
                csrf_token=_csrf_token(session),
            ),
        )
        _set_frontend_cookies(response=response, security=security, session=session)
        return response

    return endpoint


def settings_page(
    settings: SettingsProvider,
    readiness: PreflightReport | None = None,
    security: SecurityContext | None = None,
) -> Callable[[Request, HTTPAuthorizationCredentials | None], HTMLResponse]:
    def endpoint(
        request: Request,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Depends(bearer_scheme),
        ] = None,
    ) -> HTMLResponse:
        current_settings = settings()
        login = _login_response_if_unauthorized(
            security=security,
            settings=current_settings,
            request=request,
            credentials=credentials,
        )
        if login is not None:
            return login
        session = _frontend_session(security=security, request=request, credentials=credentials)
        response = HTMLResponse(
            content=render_settings_page(
                settings=current_settings,
                readiness=readiness,
                csrf_token=_csrf_token(session),
            ),
        )
        _set_frontend_cookies(response=response, security=security, session=session)
        return response

    return endpoint


def logs_page(
    settings: SettingsProvider,
    logs: tuple[LogEntryResponse, ...],
    security: SecurityContext | None = None,
) -> Callable[[Request, HTTPAuthorizationCredentials | None], HTMLResponse]:
    def endpoint(
        request: Request,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Depends(bearer_scheme),
        ] = None,
    ) -> HTMLResponse:
        current_settings = settings()
        login = _login_response_if_unauthorized(
            security=security,
            settings=current_settings,
            request=request,
            credentials=credentials,
        )
        if login is not None:
            return login
        session = _frontend_session(security=security, request=request, credentials=credentials)
        response = HTMLResponse(
            content=render_logs_page(
                settings=current_settings,
                logs=logs,
                csrf_token=_csrf_token(session),
            ),
        )
        _set_frontend_cookies(response=response, security=security, session=session)
        return response

    return endpoint


def _login_response_if_unauthorized(
    *,
    security: SecurityContext | None,
    settings: RuntimeSettings,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> HTMLResponse | None:
    try:
        _require_page_access(security=security, request=request, credentials=credentials)
    except HTTPException as exc:
        if exc.status_code != status.HTTP_401_UNAUTHORIZED:
            raise
        return HTMLResponse(
            content=render_login_page(settings=settings),
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    return None


def _require_page_access(
    *,
    security: SecurityContext | None,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> None:
    if security is None:
        return
    security.require_operator(request, credentials)


def _frontend_session(
    *,
    security: SecurityContext | None,
    request: Request,
    credentials: HTTPAuthorizationCredentials | None,
) -> SecuritySession | None:
    if security is None:
        return None
    return security.frontend_session(request, credentials)


def _csrf_token(session: SecuritySession | None) -> str:
    if session is None:
        return ""
    return session.csrf_token


async def _read_models(store: DashboardReadStore | None) -> DashboardReadModels:
    if store is None:
        return DashboardReadModels.empty()
    return await store.read_models()


def _set_frontend_cookies(
    *,
    response: HTMLResponse,
    security: SecurityContext | None,
    session: SecuritySession | None,
) -> None:
    if security is None or session is None:
        return
    security.set_session_cookies(response, session)
