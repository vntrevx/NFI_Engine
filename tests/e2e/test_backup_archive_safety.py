from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Final
from zipfile import ZIP_DEFLATED, ZipFile

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _write_traversal_archive(archive_path: Path) -> None:
    payload = b"unsafe"
    manifest = {
        "engine_version": "test",
        "generated_at": "2026-06-17T00:00:00+00:00",
        "redacted": True,
        "config_hash": "",
        "dependency_lock_hash": "",
        "files": ["../../outside.txt"],
        "checksums": {"../../outside.txt": hashlib.sha256(payload).hexdigest()},
    }
    with ZipFile(archive_path, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest).encode())
        archive.writestr("../../outside.txt", payload)


def _write_manifest_only_archive(archive_path: Path) -> None:
    files: tuple[str, ...] = ()
    checksums: dict[str, str] = {}
    manifest = {
        "engine_version": "test",
        "generated_at": "2026-06-17T00:00:00+00:00",
        "redacted": True,
        "config_hash": "",
        "dependency_lock_hash": "",
        "files": files,
        "checksums": checksums,
    }
    with ZipFile(archive_path, mode="w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest).encode())


def _tamper_config_member(archive_path: Path) -> None:
    with ZipFile(archive_path) as archive:
        members = tuple(
            (name, b"{}" if name == "config.json" else archive.read(name))
            for name in archive.namelist()
        )
    with ZipFile(archive_path, mode="w", compression=ZIP_DEFLATED) as archive:
        for name, data in members:
            archive.writestr(name, data)


def test_backup_verify_and_restore_reject_traversal_archive_members(tmp_path: Path) -> None:
    # Given: a crafted archive with a traversal member in its manifest.
    archive_path = tmp_path / "traversal.zip"
    _write_traversal_archive(archive_path)

    # When: the operator asks the real CLI to verify or rehearse restore.
    verify = _run_command(["uv", "run", "nfi-engine", "backup", "verify", str(archive_path)])
    restore = _run_command(
        ["uv", "run", "nfi-engine", "backup", "restore", "--dry-run", str(archive_path)],
    )

    # Then: both surfaces fail closed without printing a restore step for the unsafe member.
    assert verify.returncode != 0
    assert restore.returncode != 0
    assert verify.stderr.startswith("BACKUP_INVALID: ")
    assert restore.stderr.startswith("BACKUP_INVALID: ")
    assert "../../outside.txt" not in verify.stdout
    assert "step=restore" not in restore.stdout


def test_backup_verify_and_restore_reject_incomplete_manifest_only_archive(
    tmp_path: Path,
) -> None:
    # Given: an allowlisted archive containing only manifest metadata.
    archive_path = tmp_path / "manifest-only.zip"
    _write_manifest_only_archive(archive_path)

    # When: the operator asks the real CLI to verify or rehearse restore.
    verify = _run_command(["uv", "run", "nfi-engine", "backup", "verify", str(archive_path)])
    restore = _run_command(
        ["uv", "run", "nfi-engine", "backup", "restore", "--dry-run", str(archive_path)],
    )

    # Then: both surfaces fail closed without printing a valid restore plan.
    assert verify.returncode != 0
    assert restore.returncode != 0
    assert verify.stderr.startswith("BACKUP_INVALID: ")
    assert restore.stderr.startswith("BACKUP_INVALID: ")
    assert "manifest_valid=true" not in verify.stdout
    assert "restore_plan=backup" not in restore.stdout


def test_backup_restore_rejects_tampered_allowlisted_archive_members(tmp_path: Path) -> None:
    # Given: a normal backup archive whose allowlisted config member is tampered afterward.
    archive_path = tmp_path / "backup.zip"
    create = _run_command(
        [
            "uv",
            "run",
            "nfi-engine",
            "backup",
            "create",
            "--config",
            "examples/futures-paper.yaml",
            "--output",
            str(archive_path),
        ],
    )
    _tamper_config_member(archive_path)

    # When: verify and restore dry-run inspect the checksum-invalid archive.
    verify = _run_command(["uv", "run", "nfi-engine", "backup", "verify", str(archive_path)])
    restore = _run_command(
        ["uv", "run", "nfi-engine", "backup", "restore", "--dry-run", str(archive_path)],
    )

    # Then: verify reports the mismatch and restore fails closed before printing steps.
    assert create.returncode == 0, create.stderr
    assert verify.returncode == 0, verify.stderr
    assert "manifest_valid=false" in verify.stdout
    assert restore.returncode != 0
    assert restore.stderr.startswith("BACKUP_INVALID: ")
    assert "step=restore" not in restore.stdout
