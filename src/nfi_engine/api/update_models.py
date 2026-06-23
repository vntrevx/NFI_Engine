from __future__ import annotations

from typing import ClassVar

from pydantic import ConfigDict

from nfi_engine.api.models import StrictApiModel
from nfi_engine.maintenance.update_provenance import (
    UPDATE_SOURCE_LOCAL_PROOF,
    UpdatePreview,
    UpdateProofPolicy,
    UpdateProofReceipt,
    UpdateRollbackState,
)


class UpdateRollbackStateResponse(StrictApiModel):
    status: str
    can_rollback: bool
    backup_reference_required: bool


class UpdatePreviewResponse(StrictApiModel):
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
    rollback_state: UpdateRollbackStateResponse


class UpdateProofRequest(StrictApiModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True, strict=True)

    backup_reference: str | None = None
    acknowledge_unverified: bool = False
    allow_dirty_worktree: bool = False
    update_source: str = UPDATE_SOURCE_LOCAL_PROOF

    def to_policy(self) -> UpdateProofPolicy:
        return UpdateProofPolicy(
            backup_reference=self.backup_reference,
            acknowledge_unverified=self.acknowledge_unverified,
            allow_dirty_worktree=self.allow_dirty_worktree,
            update_source=self.update_source,
        )


class UpdateProofReceiptResponse(StrictApiModel):
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


def update_preview_response(preview: UpdatePreview) -> UpdatePreviewResponse:
    return UpdatePreviewResponse(
        engine_version=preview.engine_version,
        strategy_name=preview.strategy_name,
        strategy_module=preview.strategy_module,
        strategy_digest=preview.strategy_digest,
        strategy_source=preview.strategy_source,
        config_digest=preview.config_digest,
        config_source=preview.config_source,
        dependency_lock_digest=preview.dependency_lock_digest,
        dependency_lock_source=preview.dependency_lock_source,
        remote_network_allowed=preview.remote_network_allowed,
        compatibility_status=preview.compatibility_status,
        provenance_verified=preview.provenance_verified,
        live_blocked=preview.live_blocked,
        workspace_state=preview.workspace_state,
        workspace_dirty=preview.workspace_dirty,
        rollback_state=update_rollback_state_response(preview.rollback_state),
    )


def update_proof_receipt_response(receipt: UpdateProofReceipt) -> UpdateProofReceiptResponse:
    return UpdateProofReceiptResponse(
        action=receipt.action,
        accepted=receipt.accepted,
        proof_only=receipt.proof_only,
        mutation_applied=receipt.mutation_applied,
        source_mutated=receipt.source_mutated,
        remote_network_allowed=receipt.remote_network_allowed,
        restart_required=receipt.restart_required,
        reload_required=receipt.reload_required,
        backup_reference=receipt.backup_reference,
        acknowledge_unverified=receipt.acknowledge_unverified,
        allow_dirty_worktree=receipt.allow_dirty_worktree,
        update_source=receipt.update_source,
        provenance_verified=receipt.provenance_verified,
        live_blocked=receipt.live_blocked,
        workspace_state=receipt.workspace_state,
        workspace_dirty=receipt.workspace_dirty,
        compatibility_status=receipt.compatibility_status,
        blocked_reasons=receipt.blocked_reasons,
    )


def update_rollback_state_response(state: UpdateRollbackState) -> UpdateRollbackStateResponse:
    return UpdateRollbackStateResponse(
        status=state.status,
        can_rollback=state.can_rollback,
        backup_reference_required=state.backup_reference_required,
    )
