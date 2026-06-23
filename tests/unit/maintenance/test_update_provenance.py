from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

from nfi_engine import __version__
from nfi_engine.config import RuntimeSettings, load_runtime_settings
from nfi_engine.config.models import StrategySettings
from nfi_engine.maintenance.update_provenance import (
    UpdateProofPolicy,
    build_update_apply_receipt,
    build_update_preview,
    build_update_rollback_receipt,
)


def test_build_update_preview_uses_local_config_and_strategy_digests() -> None:
    # Given: a locally backed config file and the in-repo demo strategy module.
    config_path = Path("examples/futures-paper.yaml")
    settings = load_runtime_settings(config_path)

    # When: local update provenance is previewed.
    preview = build_update_preview(
        settings=settings, config_path=config_path, workspace_root=Path.cwd()
    )

    # Then: the preview reports locally provable digests and a rollback requirement.
    assert preview.engine_version == __version__
    assert preview.strategy_name == settings.strategy.name
    assert preview.strategy_module == settings.strategy.module
    assert preview.strategy_digest != "unavailable"
    assert preview.config_source == str(config_path)
    assert preview.config_digest == hashlib.sha256(config_path.read_bytes()).hexdigest()
    assert preview.dependency_lock_source == "uv.lock"
    assert preview.remote_network_allowed is False
    assert preview.provenance_verified is True
    assert preview.compatibility_status == "local_verified"
    assert preview.live_blocked is False
    assert preview.rollback_state.status == "backup_required"
    assert preview.rollback_state.can_rollback is False


def test_preview_uses_redacted_runtime_digest_when_local_proof_is_missing() -> None:
    # Given: runtime settings whose strategy module cannot be proven from local files.
    settings = RuntimeSettings(
        strategy=StrategySettings(
            name="MissingStrategy",
            module="nfi_engine.strategy.missing:MissingStrategy",
        ),
    )

    # When: update provenance is previewed without a config file path.
    preview = build_update_preview(settings=settings, config_path=None, workspace_root=Path.cwd())

    # Then: the preview stays local-safe but marks provenance as unverified.
    assert preview.strategy_digest == "unavailable"
    assert preview.config_source == "runtime_redacted"
    assert preview.provenance_verified is False
    assert preview.compatibility_status == "unverified_local"
    assert preview.live_blocked is True


def test_apply_receipt_blocks_without_backup_reference_or_unverified_acknowledgement() -> None:
    # Given: an unverified local preview built from runtime-only settings.
    preview = build_update_preview(
        settings=RuntimeSettings(), config_path=None, workspace_root=Path.cwd()
    )

    # When: apply proof is requested without backup evidence or acknowledgement.
    receipt = build_update_apply_receipt(
        preview=preview,
        policy=UpdateProofPolicy(
            backup_reference=None,
            acknowledge_unverified=False,
            allow_dirty_worktree=False,
            update_source="local_proof",
        ),
    )

    # Then: the request is returned as a typed blocked receipt instead of mutating anything.
    assert receipt.action == "apply"
    assert receipt.accepted is False
    assert receipt.proof_only is True
    assert receipt.mutation_applied is False
    assert receipt.source_mutated is False
    assert receipt.remote_network_allowed is False
    assert receipt.restart_required is False
    assert receipt.reload_required is False
    assert "backup_reference_required" in receipt.blocked_reasons
    assert "acknowledge_unverified_required" in receipt.blocked_reasons


def test_rollback_receipt_accepts_verified_local_proof_with_backup_reference() -> None:
    # Given: a verified local preview and a backup reference.
    config_path = Path("examples/futures-paper.yaml")
    preview = build_update_preview(
        settings=load_runtime_settings(config_path),
        config_path=config_path,
        workspace_root=Path.cwd(),
    )

    # When: rollback proof is requested with backup evidence.
    receipt = build_update_rollback_receipt(
        preview=preview,
        policy=UpdateProofPolicy(
            backup_reference="backups/local-proof.zip",
            acknowledge_unverified=False,
            allow_dirty_worktree=True,
            update_source="local_proof",
        ),
    )

    # Then: the API can issue a proof receipt without mutating runtime config.
    assert receipt.action == "rollback"
    assert receipt.accepted is True
    assert receipt.proof_only is True
    assert receipt.mutation_applied is False
    assert receipt.backup_reference == "backups/local-proof.zip"
    assert receipt.blocked_reasons == ()


def test_apply_receipt_blocks_dirty_workspace_without_explicit_policy() -> None:
    # Given: a verified preview whose source checkout has uncommitted changes.
    config_path = Path("examples/futures-paper.yaml")
    preview = build_update_preview(
        settings=load_runtime_settings(config_path),
        config_path=config_path,
        workspace_root=Path.cwd(),
    )
    dirty_preview = replace(preview, workspace_dirty=True, workspace_state="dirty")

    # When: apply proof is requested with and without the dirty-worktree override.
    blocked = build_update_apply_receipt(
        preview=dirty_preview,
        policy=UpdateProofPolicy(
            backup_reference="backups/local-proof.zip",
            acknowledge_unverified=False,
            allow_dirty_worktree=False,
            update_source="local_proof",
        ),
    )
    allowed = build_update_apply_receipt(
        preview=dirty_preview,
        policy=UpdateProofPolicy(
            backup_reference="backups/local-proof.zip",
            acknowledge_unverified=False,
            allow_dirty_worktree=True,
            update_source="local_proof",
        ),
    )

    # Then: dirty source requires an explicit proof policy.
    assert blocked.accepted is False
    assert "workspace_dirty" in blocked.blocked_reasons
    assert "workspace_dirty" not in allowed.blocked_reasons


def test_rollback_receipt_blocks_invalid_update_source() -> None:
    # Given: a verified local preview.
    config_path = Path("examples/futures-paper.yaml")
    preview = build_update_preview(
        settings=load_runtime_settings(config_path),
        config_path=config_path,
        workspace_root=Path.cwd(),
    )

    # When: rollback proof claims a non-local update source.
    receipt = build_update_rollback_receipt(
        preview=preview,
        policy=UpdateProofPolicy(
            backup_reference="backups/local-proof.zip",
            acknowledge_unverified=False,
            allow_dirty_worktree=True,
            update_source="remote_plugin",
        ),
    )

    # Then: the request is blocked before any source mutation path can exist.
    assert receipt.accepted is False
    assert receipt.source_mutated is False
    assert "invalid_update_source" in receipt.blocked_reasons
