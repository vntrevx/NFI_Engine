from __future__ import annotations

import hashlib
from dataclasses import dataclass
from importlib.util import find_spec
from pathlib import Path
from typing import Final

from nfi_engine import __version__
from nfi_engine.api.models import config_current_response
from nfi_engine.config import RuntimeSettings
from nfi_engine.maintenance.update_workspace import (
    WORKSPACE_STATE_DIRTY,
    detect_update_workspace_state,
)

UNAVAILABLE_DIGEST: Final = "unavailable"
RUNTIME_REDACTED_SOURCE: Final = "runtime_redacted"
SOURCE_MUTATED: Final = False
REMOTE_NETWORK_ALLOWED: Final = False
RESTART_REQUIRED: Final = False
RELOAD_REQUIRED: Final = False
HASH_CHUNK_SIZE: Final = 1024 * 1024
UPDATE_SOURCE_LOCAL_PROOF: Final = "local_proof"


@dataclass(frozen=True, slots=True)
class UpdateRollbackState:
    status: str
    can_rollback: bool
    backup_reference_required: bool


@dataclass(frozen=True, slots=True)
class UpdateProofPolicy:
    backup_reference: str | None
    acknowledge_unverified: bool
    allow_dirty_worktree: bool
    update_source: str


@dataclass(frozen=True, slots=True)
class UpdatePreview:
    engine_version: str
    strategy_name: str
    strategy_module: str
    strategy_digest: str
    strategy_source: str
    config_digest: str
    config_source: str
    dependency_lock_digest: str
    dependency_lock_source: str
    remote_network_allowed: bool
    compatibility_status: str
    provenance_verified: bool
    live_blocked: bool
    workspace_state: str
    workspace_dirty: bool
    rollback_state: UpdateRollbackState


@dataclass(frozen=True, slots=True)
class UpdateProofReceipt:
    action: str
    accepted: bool
    proof_only: bool
    mutation_applied: bool
    source_mutated: bool
    remote_network_allowed: bool
    restart_required: bool
    reload_required: bool
    backup_reference: str | None
    acknowledge_unverified: bool
    allow_dirty_worktree: bool
    update_source: str
    provenance_verified: bool
    live_blocked: bool
    workspace_state: str
    workspace_dirty: bool
    compatibility_status: str
    blocked_reasons: tuple[str, ...]


def build_update_preview(
    *,
    settings: RuntimeSettings,
    config_path: Path | None,
    workspace_root: Path,
) -> UpdatePreview:
    strategy_source, strategy_digest = _strategy_provenance(settings)
    config_source, config_digest = _config_provenance(settings=settings, config_path=config_path)
    lock_source, lock_digest = _dependency_lock_provenance(workspace_root)
    workspace_state = detect_update_workspace_state(workspace_root)
    provenance_verified = (
        strategy_digest != UNAVAILABLE_DIGEST and config_source != RUNTIME_REDACTED_SOURCE
    )
    compatibility_status = _compatibility_status(
        live_trading=settings.engine.live_trading,
        provenance_verified=provenance_verified,
    )
    return UpdatePreview(
        engine_version=__version__,
        strategy_name=settings.strategy.name,
        strategy_module=settings.strategy.module,
        strategy_digest=strategy_digest,
        strategy_source=strategy_source,
        config_digest=config_digest,
        config_source=config_source,
        dependency_lock_digest=lock_digest,
        dependency_lock_source=lock_source,
        remote_network_allowed=REMOTE_NETWORK_ALLOWED,
        compatibility_status=compatibility_status,
        provenance_verified=provenance_verified,
        live_blocked=settings.engine.live_trading or not provenance_verified,
        workspace_state=workspace_state,
        workspace_dirty=workspace_state == WORKSPACE_STATE_DIRTY,
        rollback_state=UpdateRollbackState(
            status="backup_required",
            can_rollback=False,
            backup_reference_required=True,
        ),
    )


def build_update_apply_receipt(
    *,
    preview: UpdatePreview,
    policy: UpdateProofPolicy,
) -> UpdateProofReceipt:
    return _build_receipt(
        action="apply",
        preview=preview,
        policy=policy,
    )


def build_update_rollback_receipt(
    *,
    preview: UpdatePreview,
    policy: UpdateProofPolicy,
) -> UpdateProofReceipt:
    return _build_receipt(
        action="rollback",
        preview=preview,
        policy=policy,
    )


def _build_receipt(
    *,
    action: str,
    preview: UpdatePreview,
    policy: UpdateProofPolicy,
) -> UpdateProofReceipt:
    blocked_reasons = _blocked_reasons(
        preview=preview,
        policy=policy,
    )
    return UpdateProofReceipt(
        action=action,
        accepted=len(blocked_reasons) == 0,
        proof_only=True,
        mutation_applied=False,
        source_mutated=SOURCE_MUTATED,
        remote_network_allowed=REMOTE_NETWORK_ALLOWED,
        restart_required=RESTART_REQUIRED,
        reload_required=RELOAD_REQUIRED,
        backup_reference=_normalized_backup_reference(policy.backup_reference),
        acknowledge_unverified=policy.acknowledge_unverified,
        allow_dirty_worktree=policy.allow_dirty_worktree,
        update_source=_normalized_update_source(policy.update_source),
        provenance_verified=preview.provenance_verified,
        live_blocked=preview.live_blocked,
        workspace_state=preview.workspace_state,
        workspace_dirty=preview.workspace_dirty,
        compatibility_status=preview.compatibility_status,
        blocked_reasons=blocked_reasons,
    )


def _blocked_reasons(
    *,
    preview: UpdatePreview,
    policy: UpdateProofPolicy,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if _normalized_update_source(policy.update_source) != UPDATE_SOURCE_LOCAL_PROOF:
        reasons.append("invalid_update_source")
    if _normalized_backup_reference(policy.backup_reference) is None:
        reasons.append("backup_reference_required")
    if not preview.provenance_verified and not policy.acknowledge_unverified:
        reasons.append("acknowledge_unverified_required")
    if preview.workspace_dirty and not policy.allow_dirty_worktree:
        reasons.append("workspace_dirty")
    if preview.compatibility_status == "live_unsafe":
        reasons.append("live_unsafe")
    return tuple(reasons)


def _strategy_provenance(settings: RuntimeSettings) -> tuple[str, str]:
    module_name = settings.strategy.module.split(":", maxsplit=1)[0]
    spec = find_spec(module_name)
    if spec is None or spec.origin is None:
        return ("unresolved", UNAVAILABLE_DIGEST)
    strategy_path = Path(spec.origin)
    if not strategy_path.exists():
        return ("unresolved", UNAVAILABLE_DIGEST)
    return (str(strategy_path), _sha256_path(strategy_path))


def _config_provenance(
    *,
    settings: RuntimeSettings,
    config_path: Path | None,
) -> tuple[str, str]:
    if config_path is None:
        payload = config_current_response(settings).model_dump_json().encode("utf-8")
        return (RUNTIME_REDACTED_SOURCE, hashlib.sha256(payload).hexdigest())
    return (str(config_path), _sha256_path(config_path))


def _dependency_lock_provenance(workspace_root: Path) -> tuple[str, str]:
    for candidate in ("uv.lock", "package-lock.json"):
        path = workspace_root / candidate
        if path.exists():
            return (candidate, _sha256_path(path))
    return ("unavailable", UNAVAILABLE_DIGEST)


def _compatibility_status(*, live_trading: bool, provenance_verified: bool) -> str:
    if live_trading:
        return "live_unsafe"
    if provenance_verified:
        return "local_verified"
    return "unverified_local"


def _normalized_backup_reference(backup_reference: str | None) -> str | None:
    if backup_reference is None:
        return None
    normalized = backup_reference.strip()
    if normalized == "":
        return None
    return normalized


def _normalized_update_source(update_source: str) -> str:
    return update_source.strip()


def _sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as opened:
        for chunk in iter(lambda: opened.read(HASH_CHUNK_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()
