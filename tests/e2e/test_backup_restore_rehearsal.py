from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Literal, assert_never
from zipfile import ZipFile

import pytest

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
REHEARSAL_PROJECT: Final = "nfi-engine-rehearsal"
PathCase = Literal["unmarked-runtime", "unsafe-home"]


@dataclass(frozen=True, slots=True)
class RehearsalArtifacts:
    runtime_dir: Path
    runtime_marker: Path
    token_file: Path
    protected_file: Path
    archive_path: Path


def _run_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def _create_rehearsal_artifacts(tmp_path: Path) -> RehearsalArtifacts:
    runtime_dir = tmp_path / "runtime"
    config_dir = runtime_dir / "config"
    config_dir.mkdir(parents=True)
    runtime_marker = runtime_dir / ".nfi-engine-runtime"
    runtime_marker.write_text("nfi-engine-runtime=1\n", encoding="utf-8")
    token_file = runtime_dir / "docker.env"
    token_file.write_text("NFI_ENGINE_API_TOKEN=rehearsal-token\n", encoding="utf-8")
    protected_file = config_dir / "operator-marker.txt"
    protected_file.write_text("rehearsal-marker\n", encoding="utf-8")
    archive_path = tmp_path / "backup-rehearsal.zip"
    return RehearsalArtifacts(
        runtime_dir=runtime_dir,
        runtime_marker=runtime_marker,
        token_file=token_file,
        protected_file=protected_file,
        archive_path=archive_path,
    )


def _rehearsal_commands(
    artifacts: RehearsalArtifacts,
) -> dict[str, list[str]]:
    return {
        "create": [
            "uv",
            "run",
            "nfi-engine",
            "backup",
            "create",
            "--config",
            "examples/futures-paper.yaml",
            "--output",
            str(artifacts.archive_path),
        ],
        "verify": ["uv", "run", "nfi-engine", "backup", "verify", str(artifacts.archive_path)],
        "restore": [
            "uv",
            "run",
            "nfi-engine",
            "backup",
            "restore",
            "--dry-run",
            str(artifacts.archive_path),
        ],
        "restore_apply": [
            "uv",
            "run",
            "nfi-engine",
            "backup",
            "restore",
            "--apply",
            str(artifacts.archive_path),
        ],
        "safe_uninstall": [
            "bash",
            "scripts/uninstall.sh",
            "--yes",
            "--runtime-dir",
            str(artifacts.runtime_dir),
            "--dry-run",
            "--project-name",
            REHEARSAL_PROJECT,
        ],
        "purge_uninstall": [
            "bash",
            "scripts/uninstall.sh",
            "--purge",
            "--yes",
            "--runtime-dir",
            str(artifacts.runtime_dir),
            "--dry-run",
            "--project-name",
            REHEARSAL_PROJECT,
        ],
    }


def _archive_payload(archive_path: Path) -> tuple[set[str], bytes]:
    with ZipFile(archive_path) as archive:
        archive_names = set(archive.namelist())
        archive_payload = b"".join(archive.read(name) for name in sorted(archive_names))
    return archive_names, archive_payload


def _assert_rehearsal_outputs(
    results: dict[str, subprocess.CompletedProcess[str]],
    artifacts: RehearsalArtifacts,
    archive_names: set[str],
    archive_payload: bytes,
) -> None:
    create = results["create"]
    verify = results["verify"]
    restore = results["restore"]
    restore_apply = results["restore_apply"]
    safe_uninstall = results["safe_uninstall"]
    purge_uninstall = results["purge_uninstall"]

    assert create.returncode == 0, create.stderr
    assert verify.returncode == 0, verify.stderr
    assert restore.returncode == 0, restore.stderr
    assert restore_apply.returncode != 0
    assert safe_uninstall.returncode == 0, safe_uninstall.stderr
    assert purge_uninstall.returncode == 0, purge_uninstall.stderr

    assert "backup_created=true" in create.stdout
    assert "manifest_valid=true" in create.stdout
    assert "redacted=true" in create.stdout
    assert "manifest_valid=true" in verify.stdout
    assert "redacted=true" in verify.stdout
    assert "restore_plan=backup" in restore.stdout
    assert "apply=false" in restore.stdout
    assert "manifest_valid=true" in restore.stdout
    assert "step=restore config.json" in restore.stdout
    assert restore_apply.stderr.startswith("BACKUP_RESTORE_APPLY_UNSUPPORTED: ")
    assert "restore_plan=backup" not in restore_apply.stdout

    assert "mode=safe" in safe_uninstall.stdout
    assert f"compose_project={REHEARSAL_PROJECT}" in safe_uninstall.stdout
    assert f"preserve_runtime={artifacts.runtime_dir}" in safe_uninstall.stdout
    assert "remove_runtime=" not in safe_uninstall.stdout
    assert "uninstall_plan=dry-run" in safe_uninstall.stdout

    assert "mode=purge" in purge_uninstall.stdout
    assert f"compose_project={REHEARSAL_PROJECT}" in purge_uninstall.stdout
    assert f"remove_runtime={artifacts.runtime_dir}" in purge_uninstall.stdout
    assert "backup_runtime=not_requested" in purge_uninstall.stdout
    assert "uninstall_plan=dry-run" in purge_uninstall.stdout

    assert {"config.json", "logs.json", "manifest.json"} <= archive_names
    assert b"rehearsal-token" not in archive_payload
    assert artifacts.runtime_marker.read_text(encoding="utf-8") == "nfi-engine-runtime=1\n"
    assert (
        artifacts.token_file.read_text(encoding="utf-8") == "NFI_ENGINE_API_TOKEN=rehearsal-token\n"
    )
    assert artifacts.protected_file.read_text(encoding="utf-8") == "rehearsal-marker\n"


def test_backup_restore_and_uninstall_dry_run_rehearsal_preserves_runtime_artifacts(
    tmp_path: Path,
) -> None:
    # Given: a marker-protected runtime directory with a generated token file.
    artifacts = _create_rehearsal_artifacts(tmp_path)

    # When: the full backup, restore rehearsal, and uninstall dry-run sequence is executed.
    results = {
        name: _run_command(command) for name, command in _rehearsal_commands(artifacts).items()
    }
    archive_names, archive_payload = _archive_payload(artifacts.archive_path)

    # Then: each CLI surface reports the rehearsal plan while runtime marker and token stay intact.
    _assert_rehearsal_outputs(results, artifacts, archive_names, archive_payload)


@pytest.mark.parametrize(
    ("path_case", "expected_code"),
    [
        pytest.param("unmarked-runtime", "UNINSTALL_RUNTIME_MARKER_MISSING", id="unmarked-runtime"),
        pytest.param("unsafe-home", "UNINSTALL_UNSAFE_RUNTIME_DIR", id="unsafe-home"),
    ],
)
def test_backup_restore_rehearsal_purge_dry_run_refuses_unsafe_runtime_paths(
    tmp_path: Path,
    path_case: PathCase,
    expected_code: str,
) -> None:
    # Given: a purge dry-run targeting an unmarked or intrinsically unsafe runtime path.
    match path_case:
        case "unmarked-runtime":
            runtime_dir = tmp_path / "operator-files"
            runtime_dir.mkdir()
        case "unsafe-home":
            runtime_dir = Path.home()
        case unreachable:
            assert_never(unreachable)

    command: Final = [
        "bash",
        "scripts/uninstall.sh",
        "--purge",
        "--yes",
        "--runtime-dir",
        str(runtime_dir),
        "--dry-run",
        "--project-name",
        REHEARSAL_PROJECT,
    ]

    # When: the destructive purge rehearsal command runs.
    result = _run_command(command)

    # Then: the command refuses before printing any removal scope and keeps stderr machine-readable.
    assert result.returncode != 0
    assert result.stderr == f"{expected_code}: {runtime_dir}\n"
    assert "remove_runtime=" not in result.stdout
