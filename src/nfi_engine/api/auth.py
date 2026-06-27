from __future__ import annotations

import secrets
from dataclasses import dataclass
from enum import StrEnum, unique
from typing import ClassVar

from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials  # noqa: TC002
from pydantic import BaseModel, ConfigDict

from nfi_engine.api.errors import ApiErrorCode
from nfi_engine.api.models import SessionLoginRequest


class ApiErrorResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    code: ApiErrorCode
    message: str
    audit_event: str | None = None


@unique
class OperatorRole(StrEnum):
    OPERATOR = "operator"
    READ_ONLY = "read_only"


@dataclass(frozen=True, slots=True)
class OperatorIdentity:
    name: str
    role: OperatorRole = OperatorRole.OPERATOR


@dataclass(frozen=True, slots=True)
class OperatorAuthenticator:
    token: str | None
    username: str = "admin"
    password: str | None = None
    anonymous_allowed: bool = False

    def require(self, credentials: HTTPAuthorizationCredentials | None) -> OperatorIdentity:
        if not self.accepts(_credential_token(credentials)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=ApiErrorResponse(
                    code=ApiErrorCode.API_AUTH_REQUIRED,
                    message="bearer token required",
                ).model_dump(mode="json"),
            )
        return OperatorIdentity(name="operator")

    def accepts(self, token: str | None) -> bool:
        if self.token is None:
            return self.anonymous_allowed and token is None
        return self.token is not None and _secret_equals(token, self.token)

    def accepts_login(self, login: SessionLoginRequest) -> bool:
        password = self.password or self.token
        if password is None:
            return self.anonymous_allowed
        return _secret_equals(login.username, self.username) and _secret_equals(
            login.password,
            password,
        )


def _credential_token(credentials: HTTPAuthorizationCredentials | None) -> str | None:
    if credentials is None:
        return None
    return credentials.credentials


def _secret_equals(left: str | None, right: str) -> bool:
    if left is None:
        return False
    return secrets.compare_digest(left, right)
