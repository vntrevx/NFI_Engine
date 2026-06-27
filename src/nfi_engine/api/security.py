from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Final, NoReturn

from fastapi import HTTPException, Request, Response, status
from fastapi.security import HTTPAuthorizationCredentials  # noqa: TC002

from nfi_engine.api.auth import (
    ApiErrorResponse,
    OperatorAuthenticator,
    OperatorIdentity,
    OperatorRole,
)
from nfi_engine.api.errors import ApiErrorCode
from nfi_engine.api.models import SessionLoginRequest
from nfi_engine.api.security_store import SecuritySession, SecuritySessionStore
from nfi_engine.api.settings import LOCAL_ENVIRONMENTS
from nfi_engine.config import RuntimeSettings

SESSION_COOKIE: Final = "nfi_engine_session"
CSRF_COOKIE: Final = "nfi_engine_csrf"
CSRF_HEADER: Final = "x-nfi-csrf-token"
READONLY_AUDIT_EVENT: Final = "READONLY_ACTION_BLOCKED"


@dataclass(frozen=True, slots=True)
class SecurityContext:
    _settings_provider: Callable[[], RuntimeSettings]
    authenticator: OperatorAuthenticator
    store: SecuritySessionStore

    @classmethod
    def from_settings(cls, settings: RuntimeSettings) -> SecurityContext:
        return cls.from_settings_provider(lambda: settings)

    @classmethod
    def from_settings_provider(
        cls,
        settings_provider: Callable[[], RuntimeSettings],
    ) -> SecurityContext:
        settings = settings_provider()
        return cls(
            _settings_provider=settings_provider,
            authenticator=OperatorAuthenticator(
                token=settings.api.auth_token,
                username=settings.api.operator_username,
                password=settings.api.operator_password,
                anonymous_allowed=(
                    settings.api.auth_token is None
                    and settings.api.operator_password is None
                    and settings.engine.environment in LOCAL_ENVIRONMENTS
                ),
            ),
            store=SecuritySessionStore(),
        )

    @property
    def settings(self) -> RuntimeSettings:
        return self._settings_provider()

    @property
    def operator_role(self) -> OperatorRole:
        if self.settings.ui.read_only:
            return OperatorRole.READ_ONLY
        return OperatorRole.OPERATOR

    def create_login_session(
        self,
        credentials: HTTPAuthorizationCredentials | None,
        login: SessionLoginRequest | None,
    ) -> SecuritySession:
        bearer_accepted = self.authenticator.accepts(_credential_token(credentials))
        login_accepted = login is not None and self.authenticator.accepts_login(login)
        if not bearer_accepted and not login_accepted:
            _raise_api_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code=ApiErrorCode.API_AUTH_REQUIRED,
                message="operator login required",
            )
        return self.store.create(
            role=self.operator_role,
            ttl_seconds=self.settings.api.session_ttl_seconds,
        )

    def create_frontend_session(self) -> SecuritySession | None:
        if not self.authenticator.accepts(None):
            return None
        return self.store.create(
            role=self.operator_role,
            ttl_seconds=self.settings.api.session_ttl_seconds,
        )

    def frontend_session(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials | None,
    ) -> SecuritySession | None:
        session = self._session_from_request(request)
        if session is not None:
            return session
        if self.authenticator.accepts(_credential_token(credentials)) or self.authenticator.accepts(
            None,
        ):
            return self.store.create(
                role=self.operator_role,
                ttl_seconds=self.settings.api.session_ttl_seconds,
            )
        return None

    def require_operator(
        self,
        request: Request,
        credentials: HTTPAuthorizationCredentials | None,
    ) -> OperatorIdentity:
        if self.authenticator.accepts(_credential_token(credentials)):
            return OperatorIdentity(name="operator", role=self.operator_role)
        session = self._session_from_request(request)
        if session is not None:
            return OperatorIdentity(name="operator", role=session.role)
        if self.authenticator.accepts(None):
            return OperatorIdentity(name="operator", role=self.operator_role)
        return _raise_api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.API_AUTH_REQUIRED,
            message="bearer token required",
        )

    def require_session(self, request: Request) -> SecuritySession:
        session_id = request.cookies.get(SESSION_COOKIE)
        if session_id is None:
            _raise_api_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code=ApiErrorCode.API_AUTH_REQUIRED,
                message="session cookie required",
            )
        session = self.store.resolve(session_id)
        if session is None:
            _raise_api_error(
                status_code=status.HTTP_401_UNAUTHORIZED,
                code=ApiErrorCode.API_AUTH_REQUIRED,
                message="session cookie required",
            )
        self._raise_if_expired(session)
        return session

    def require_csrf(self, request: Request) -> None:
        if not self.settings.api.csrf_enabled:
            return
        token = request.headers.get(CSRF_HEADER)
        session_id = request.cookies.get(SESSION_COOKIE)
        if token is None or session_id is None:
            _raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code=ApiErrorCode.CSRF_TOKEN_REQUIRED,
                message="csrf token required",
            )
        session = self.store.resolve(session_id)
        if session is None:
            _raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code=ApiErrorCode.CSRF_TOKEN_INVALID,
                message="csrf token invalid",
            )
        self._raise_if_expired(session)
        if token != session.csrf_token:
            _raise_api_error(
                status_code=status.HTTP_403_FORBIDDEN,
                code=ApiErrorCode.CSRF_TOKEN_INVALID,
                message="csrf token invalid",
            )

    def require_write(self, request: Request) -> None:
        if not self.settings.ui.read_only:
            return
        record = self.store.audit(
            code=READONLY_AUDIT_EVENT,
            route=request.url.path,
            role=OperatorRole.READ_ONLY,
        )
        _raise_api_error(
            status_code=status.HTTP_403_FORBIDDEN,
            code=ApiErrorCode.READONLY_ACTION_BLOCKED,
            message="read-only mode blocks changes",
            audit_event=record.code,
        )

    def set_session_cookies(self, response: Response, session: SecuritySession) -> None:
        max_age = max(self.settings.api.session_ttl_seconds, 1)
        response.set_cookie(
            SESSION_COOKIE,
            session.session_id,
            max_age=max_age,
            httponly=True,
            samesite="strict",
        )
        response.set_cookie(
            CSRF_COOKIE,
            session.csrf_token,
            max_age=max_age,
            httponly=False,
            samesite="strict",
        )

    def clear_session_cookies(self, response: Response) -> None:
        response.delete_cookie(SESSION_COOKIE)
        response.delete_cookie(CSRF_COOKIE)

    def logout(self, request: Request, response: Response) -> None:
        session_id = request.cookies.get(SESSION_COOKIE)
        if session_id is not None:
            self.store.delete(session_id)
        self.clear_session_cookies(response)

    def accepts_session_id(self, session_id: str | None) -> bool:
        if session_id is None:
            return False
        session = self.store.resolve(session_id)
        if session is None:
            return False
        if session.expires_at > datetime.now(UTC):
            return True
        self.store.delete(session.session_id)
        return False

    def _session_from_request(self, request: Request) -> SecuritySession | None:
        session_id = request.cookies.get(SESSION_COOKIE)
        if session_id is None:
            return None
        session = self.store.resolve(session_id)
        if session is None:
            return None
        self._raise_if_expired(session)
        return session

    def _raise_if_expired(self, session: SecuritySession) -> None:
        if session.expires_at > datetime.now(UTC):
            return
        self.store.delete(session.session_id)
        _raise_api_error(
            status_code=status.HTTP_401_UNAUTHORIZED,
            code=ApiErrorCode.SESSION_EXPIRED,
            message="operator session expired",
        )


def _credential_token(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    if credentials is None:
        return None
    return credentials.credentials


def _raise_api_error(
    *,
    status_code: int,
    code: ApiErrorCode,
    message: str,
    audit_event: str | None = None,
) -> NoReturn:
    raise HTTPException(
        status_code=status_code,
        detail=ApiErrorResponse(
            code=code,
            message=message,
            audit_event=audit_event,
        ).model_dump(mode="json"),
    )
