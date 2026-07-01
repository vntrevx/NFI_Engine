from __future__ import annotations

from datetime import UTC, datetime

from nfi_engine.api.models import StrictApiModel
from nfi_engine.api.wallet_models import WalletBalanceResponse
from nfi_engine.runtime_health import (
    RuntimeDatabaseSnapshot,
    RuntimeHealthCheck,
    RuntimeHealthSnapshot,
    RuntimeResourceSnapshot,
)
from nfi_engine.strategy.nfi_x7 import X7SemanticStatus


class RuntimeHealthCheckResponse(StrictApiModel):
    code: str
    state: str
    message: str
    next_action: str

    @classmethod
    def from_check(cls, check: RuntimeHealthCheck) -> RuntimeHealthCheckResponse:
        return cls(
            code=check.code.value,
            state=check.state.value,
            message=check.message,
            next_action=check.next_action,
        )


class RuntimeResourceResponse(StrictApiModel):
    captured_at: str
    free_disk_bytes: int
    memory_rss_bytes: int
    disk_state: str
    memory_state: str

    @classmethod
    def from_snapshot(cls, snapshot: RuntimeResourceSnapshot) -> RuntimeResourceResponse:
        return cls(
            captured_at=_datetime_json(snapshot.captured_at),
            free_disk_bytes=snapshot.free_disk_bytes,
            memory_rss_bytes=snapshot.memory_rss_bytes,
            disk_state=snapshot.disk_state.value,
            memory_state=snapshot.memory_state.value,
        )


class RuntimeDatabaseResponse(StrictApiModel):
    captured_at: str
    readable: bool
    writable: bool
    state: str
    message: str

    @classmethod
    def from_snapshot(cls, snapshot: RuntimeDatabaseSnapshot) -> RuntimeDatabaseResponse:
        return cls(
            captured_at=_datetime_json(snapshot.captured_at),
            readable=snapshot.readable,
            writable=snapshot.writable,
            state=snapshot.state.value,
            message=snapshot.message,
        )


class X7SemanticStatusResponse(StrictApiModel):
    enabled: bool
    coverage_state: str
    observed_upstream_version: str
    provenance_evidence_path: str
    covered_modules: tuple[str, ...]
    pending_modules: tuple[str, ...]
    latest_signal_reason: str
    warmup_state: str
    missing_data_state: str
    live_readiness: str
    blocked_reason: str | None
    next_action: str

    @classmethod
    def from_status(cls, status: X7SemanticStatus) -> X7SemanticStatusResponse:
        return cls(
            enabled=status.enabled,
            coverage_state=status.coverage_state.value,
            observed_upstream_version=status.observed_upstream_version,
            provenance_evidence_path=status.provenance_evidence_path,
            covered_modules=status.covered_modules,
            pending_modules=status.pending_modules,
            latest_signal_reason=status.latest_signal_reason,
            warmup_state=status.warmup_state,
            missing_data_state=status.missing_data_state,
            live_readiness=status.live_readiness.value,
            blocked_reason=status.blocked_reason,
            next_action=status.next_action,
        )


class RuntimeHealthResponse(StrictApiModel):
    generated_at: str
    state: str
    next_action: str
    checks: tuple[RuntimeHealthCheckResponse, ...]
    resources: RuntimeResourceResponse
    database: RuntimeDatabaseResponse
    wallet_balance: WalletBalanceResponse
    x7_semantic_status: X7SemanticStatusResponse

    @classmethod
    def from_snapshot(cls, snapshot: RuntimeHealthSnapshot) -> RuntimeHealthResponse:
        return cls(
            generated_at=_datetime_json(snapshot.generated_at),
            state=snapshot.state.value,
            next_action=snapshot.next_action,
            checks=tuple(RuntimeHealthCheckResponse.from_check(check) for check in snapshot.checks),
            resources=RuntimeResourceResponse.from_snapshot(snapshot.resources),
            database=RuntimeDatabaseResponse.from_snapshot(snapshot.database),
            wallet_balance=WalletBalanceResponse.from_snapshot(snapshot.wallet_balance),
            x7_semantic_status=X7SemanticStatusResponse.from_status(snapshot.x7_semantic_status),
        )


def _datetime_json(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")
