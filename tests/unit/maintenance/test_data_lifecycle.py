from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

from nfi_engine.config.models import (
    ApiSettings,
    DatabaseSettings,
    ExchangeSettings,
    NotificationSettings,
    RuntimeSettings,
)
from nfi_engine.events import REDACTED_TEXT
from nfi_engine.maintenance.data_lifecycle import (
    DATA_LIFECYCLE_CONFIRM_SCOPE,
    DATA_LIFECYCLE_CONFIRMATION_REQUIRED,
    DataLifecyclePrunePolicy,
    build_data_lifecycle_export,
    build_data_lifecycle_footprint,
    build_data_lifecycle_prune_receipt,
)


def test_data_lifecycle_footprint_counts_runtime_artifacts(tmp_path: Path) -> None:
    # Given: a temp runtime with one file in each operator-owned category.
    settings = _settings(tmp_path)
    _runtime_file(tmp_path, "engine.sqlite3", b"sqlite")
    _runtime_file(tmp_path, "logs/engine.log", b"log")
    _runtime_file(tmp_path, "backups/backup.zip", b"backup")
    _runtime_file(tmp_path, "support-bundles/support.zip", b"support")
    _runtime_file(tmp_path, "evidence/operator.json", b"evidence")

    # When: the lifecycle footprint is built from typed settings.
    footprint = build_data_lifecycle_footprint(
        settings=settings,
        config_path=tmp_path / "config.yaml",
        workspace_root=tmp_path,
    )

    # Then: every category has bounded byte and file counts.
    counts = {category.name: category.file_count for category in footprint.categories}
    assert counts == {
        "sqlite": 1,
        "logs": 1,
        "backups": 1,
        "support_bundles": 1,
        "evidence": 1,
    }
    assert footprint.total_bytes == sum(category.total_bytes for category in footprint.categories)


def test_data_lifecycle_export_redacts_runtime_profile_secrets(tmp_path: Path) -> None:
    # Given: settings that contain exchange, API, and webhook secrets.
    settings = _settings(tmp_path)
    _runtime_file(tmp_path, "logs/engine.log", b"secret should not leak")

    # When: the redacted local profile export is built.
    export = build_data_lifecycle_export(
        settings=settings,
        config_path=tmp_path / "config.yaml",
        workspace_root=tmp_path,
    )
    merged = export.redacted_config_json + export.redacted_profile_json

    # Then: known raw secrets are absent and redacted markers remain.
    assert REDACTED_TEXT in merged
    assert "exchange-key-fixture" not in merged
    assert "exchange-secret-fixture" not in merged
    assert "operator-token-fixture" not in merged
    assert "https://hooks.example.invalid/raw-token" not in merged
    assert export.receipt_id.startswith("data-export-")


def test_data_lifecycle_footprint_skips_broken_symlink(tmp_path: Path) -> None:
    # Given: a broken symlink in an operator-owned runtime folder.
    settings = _settings(tmp_path)
    log_link = tmp_path / "logs" / "broken.log"
    log_link.parent.mkdir(parents=True, exist_ok=True)
    log_link.symlink_to(tmp_path / "logs" / "missing.log")

    # When: the lifecycle footprint scans local files.
    footprint = build_data_lifecycle_footprint(
        settings=settings,
        config_path=tmp_path / "config.yaml",
        workspace_root=tmp_path,
    )
    logs = next(category for category in footprint.categories if category.name == "logs")

    # Then: the endpoint can report the artifact without making it deletable.
    assert logs.file_count == 1
    assert logs.items[0].status == "skipped"
    assert logs.items[0].reason == "stat_failed"


def test_data_lifecycle_footprint_bounds_category_scans(tmp_path: Path) -> None:
    # Given: more logs than the operator UI should enumerate on low-resource hosts.
    settings = _settings(tmp_path)
    for index in range(505):
        _runtime_file(tmp_path, f"logs/{index}.log", b"x")

    # When: the lifecycle footprint scans local files.
    footprint = build_data_lifecycle_footprint(
        settings=settings,
        config_path=tmp_path / "config.yaml",
        workspace_root=tmp_path,
    )
    logs = next(category for category in footprint.categories if category.name == "logs")

    # Then: the response stays bounded and records the truncation.
    assert logs.file_count == 500
    assert len(logs.items) == 501
    assert logs.items[-1].status == "skipped"
    assert logs.items[-1].reason == "scan_truncated"


def test_data_lifecycle_prune_requires_preview_token_before_apply(tmp_path: Path) -> None:
    # Given: an old runtime log that is safe to prune after preview.
    settings = _settings(tmp_path)
    old_log = _runtime_file(tmp_path, "logs/old.log", b"old")
    _mark_old(old_log)

    # When: dry-run and apply receipts are requested.
    dry_run = build_data_lifecycle_prune_receipt(
        settings=settings,
        config_path=tmp_path / "config.yaml",
        workspace_root=tmp_path,
        policy=DataLifecyclePrunePolicy(retention_days=7, dry_run=True, apply=False),
    )
    blocked_apply = build_data_lifecycle_prune_receipt(
        settings=settings,
        config_path=tmp_path / "config.yaml",
        workspace_root=tmp_path,
        policy=DataLifecyclePrunePolicy(retention_days=7, dry_run=False, apply=True),
    )

    # Then: preview and missing-token apply do not mutate the file.
    assert dry_run.accepted is True
    assert dry_run.mutation_applied is False
    assert old_log.exists()
    assert blocked_apply.accepted is False
    assert "preview_token_required" in blocked_apply.blocked_reasons
    assert DATA_LIFECYCLE_CONFIRMATION_REQUIRED in blocked_apply.blocked_reasons
    assert old_log.exists()

    missing_confirmation = build_data_lifecycle_prune_receipt(
        settings=settings,
        config_path=tmp_path / "config.yaml",
        workspace_root=tmp_path,
        policy=DataLifecyclePrunePolicy(
            retention_days=7,
            dry_run=False,
            apply=True,
            preview_token=dry_run.preview_token,
        ),
    )

    assert missing_confirmation.accepted is False
    assert DATA_LIFECYCLE_CONFIRMATION_REQUIRED in missing_confirmation.blocked_reasons
    assert old_log.exists()

    applied = build_data_lifecycle_prune_receipt(
        settings=settings,
        config_path=tmp_path / "config.yaml",
        workspace_root=tmp_path,
        policy=DataLifecyclePrunePolicy(
            retention_days=7,
            dry_run=False,
            apply=True,
            preview_token=dry_run.preview_token,
            confirm_scope=DATA_LIFECYCLE_CONFIRM_SCOPE,
        ),
    )

    # Then: only the explicit apply with a matching token mutates the file.
    assert applied.accepted is True
    assert applied.mutation_applied is True
    assert not old_log.exists()
    assert applied.deleted_count == 1


def test_data_lifecycle_prune_reports_zero_byte_file_mutation(tmp_path: Path) -> None:
    # Given: an old zero-byte log that is safe to prune after preview.
    settings = _settings(tmp_path)
    old_log = _runtime_file(tmp_path, "logs/empty.log", b"")
    _mark_old(old_log)
    dry_run = build_data_lifecycle_prune_receipt(
        settings=settings,
        config_path=tmp_path / "config.yaml",
        workspace_root=tmp_path,
        policy=DataLifecyclePrunePolicy(retention_days=7, dry_run=True, apply=False),
    )

    # When: the matching apply receipt is requested.
    applied = build_data_lifecycle_prune_receipt(
        settings=settings,
        config_path=tmp_path / "config.yaml",
        workspace_root=tmp_path,
        policy=DataLifecyclePrunePolicy(
            retention_days=7,
            dry_run=False,
            apply=True,
            preview_token=dry_run.preview_token,
            confirm_scope=DATA_LIFECYCLE_CONFIRM_SCOPE,
        ),
    )

    # Then: the mutation is true even though reclaimed bytes are zero.
    assert applied.accepted is True
    assert applied.mutation_applied is True
    assert applied.deleted_count == 1
    assert applied.bytes_deleted == 0
    assert not old_log.exists()


def _settings(runtime_root: Path) -> RuntimeSettings:
    return RuntimeSettings(
        database=DatabaseSettings(url=f"sqlite+aiosqlite:///{runtime_root / 'engine.sqlite3'}"),
        exchange=ExchangeSettings(
            api_key="exchange-key-fixture",
            api_secret=_fixture_secret("exchange-secret-fixture"),
        ),
        api=ApiSettings(auth_token=_fixture_secret("operator-token-fixture")),
        notifications=NotificationSettings(
            webhook_url="https://hooks.example.invalid/raw-token",
            jsonl_path=str(runtime_root / "evidence" / "notifications.jsonl"),
        ),
    )


def _fixture_secret(value: str) -> str:
    return value


def _runtime_file(root: Path, relative: str, data: bytes) -> Path:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path


def _mark_old(path: Path) -> None:
    old = datetime.now(UTC) - timedelta(days=30)
    timestamp = old.timestamp()
    os.utime(path, (timestamp, timestamp))
