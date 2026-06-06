from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from nfi_engine.api.models import LogEntryResponse
from nfi_engine.api.security import SecurityContext
from nfi_engine.api.security_store import SecuritySession
from nfi_engine.config import RuntimeSettings
from nfi_engine.ui import render_logs_page, render_settings_page

if TYPE_CHECKING:
    from nfi_engine.preflight.models import PreflightReport

bearer_scheme = HTTPBearer(auto_error=False)


def settings_page(
    settings: RuntimeSettings,
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
        _require_page_access(security=security, request=request, credentials=credentials)
        session = _frontend_session(security=security, request=request, credentials=credentials)
        response = HTMLResponse(
            content=render_settings_page(
                settings=settings,
                readiness=readiness,
                csrf_token=_csrf_token(session),
            ),
        )
        _set_frontend_cookies(response=response, security=security, session=session)
        return response

    return endpoint


def logs_page(
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
        _require_page_access(security=security, request=request, credentials=credentials)
        session = _frontend_session(security=security, request=request, credentials=credentials)
        response = HTMLResponse(
            content=render_logs_page(logs=logs, csrf_token=_csrf_token(session)),
        )
        _set_frontend_cookies(response=response, security=security, session=session)
        return response

    return endpoint


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


def _set_frontend_cookies(
    *,
    response: HTMLResponse,
    security: SecurityContext | None,
    session: SecuritySession | None,
) -> None:
    if security is None or session is None:
        return
    security.set_session_cookies(response, session)
