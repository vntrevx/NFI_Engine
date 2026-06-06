from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from nfi_engine.api.models import (
    SecurityAuditLogResponse,
    SecuritySessionResponse,
    SessionLogoutResponse,
)
from nfi_engine.api.security import SecurityContext

if TYPE_CHECKING:
    from fastapi import APIRouter

bearer_scheme = HTTPBearer(auto_error=False)


def add_security_routes(router: APIRouter, security: SecurityContext) -> None:
    router.add_api_route("/session/login", _login(security), methods=["POST"])
    router.add_api_route("/session/logout", _logout(security), methods=["POST"])
    router.add_api_route("/session/current", _current(security), methods=["GET"])


def add_security_audit_route(router: APIRouter, security: SecurityContext) -> None:
    router.add_api_route("/security/audit", _audit(security), methods=["GET"])


def _login(
    security: SecurityContext,
) -> Callable[[Response, HTTPAuthorizationCredentials | None], SecuritySessionResponse]:
    def endpoint(
        response: Response,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Depends(bearer_scheme),
        ] = None,
    ) -> SecuritySessionResponse:
        session = security.create_login_session(credentials)
        security.set_session_cookies(response, session)
        return SecuritySessionResponse(
            role=session.role.value,
            csrf_token=session.csrf_token,
            expires_at=session.expires_at,
        )

    return endpoint


def _logout(security: SecurityContext) -> Callable[[Request, Response], SessionLogoutResponse]:
    def endpoint(request: Request, response: Response) -> SessionLogoutResponse:
        security.require_csrf(request)
        security.logout(request, response)
        return SessionLogoutResponse(logged_out=True)

    return endpoint


def _current(security: SecurityContext) -> Callable[[Request], SecuritySessionResponse]:
    def endpoint(request: Request) -> SecuritySessionResponse:
        session = security.require_session(request)
        return SecuritySessionResponse(
            role=session.role.value,
            csrf_token=session.csrf_token,
            expires_at=session.expires_at,
        )

    return endpoint


def _audit(security: SecurityContext) -> Callable[[], SecurityAuditLogResponse]:
    def endpoint() -> SecurityAuditLogResponse:
        return SecurityAuditLogResponse(
            items=tuple(record.to_response() for record in security.store.audit_log()),
        )

    return endpoint
