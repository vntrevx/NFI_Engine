from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from nfi_engine.api.auth import OperatorRole
from nfi_engine.api.models import SecurityAuditEventResponse


@dataclass(frozen=True, slots=True)
class SecuritySession:
    session_id: str
    csrf_token: str
    role: OperatorRole
    expires_at: datetime


@dataclass(frozen=True, slots=True)
class SecurityAuditRecord:
    code: str
    route: str
    role: OperatorRole

    def to_response(self) -> SecurityAuditEventResponse:
        return SecurityAuditEventResponse(
            code=self.code,
            route=self.route,
            role=self.role.value,
        )


@dataclass(slots=True)
class SecuritySessionStore:
    """Mutable in-memory session and audit store for the local operator process."""

    sessions: dict[str, SecuritySession] = field(default_factory=dict)
    audit_records: list[SecurityAuditRecord] = field(default_factory=list)

    def create(self, *, role: OperatorRole, ttl_seconds: int) -> SecuritySession:
        session = SecuritySession(
            session_id=secrets.token_urlsafe(32),
            csrf_token=secrets.token_urlsafe(32),
            role=role,
            expires_at=datetime.now(UTC) + timedelta(seconds=ttl_seconds),
        )
        self.sessions[session.session_id] = session
        return session

    def resolve(self, session_id: str) -> SecuritySession | None:
        return self.sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def audit(self, *, code: str, route: str, role: OperatorRole) -> SecurityAuditRecord:
        record = SecurityAuditRecord(code=code, route=route, role=role)
        self.audit_records.append(record)
        return record

    def audit_log(self) -> tuple[SecurityAuditRecord, ...]:
        return tuple(self.audit_records)
