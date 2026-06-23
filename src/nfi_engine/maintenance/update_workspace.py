from __future__ import annotations

from pathlib import Path
from subprocess import TimeoutExpired, run
from typing import Final

WORKSPACE_STATE_CLEAN: Final = "clean"
WORKSPACE_STATE_DIRTY: Final = "dirty"
WORKSPACE_STATE_UNAVAILABLE: Final = "unavailable"

_GIT_STATUS_TIMEOUT_SECONDS: Final = 5
_UPDATE_STATUS_PATHS: Final = (
    "src",
    "tests",
    "docs",
    "examples",
    "scripts",
    "README.md",
    "pyproject.toml",
    "uv.lock",
    "package.json",
    "package-lock.json",
    "compose.yaml",
    "Dockerfile",
)


def detect_update_workspace_state(workspace_root: Path) -> str:
    if not (workspace_root / ".git").exists():
        return WORKSPACE_STATE_UNAVAILABLE
    command = (
        "git",
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
        "--",
        *_UPDATE_STATUS_PATHS,
    )
    try:
        completed = run(  # noqa: S603 - fixed git status argv, no shell.
            command,
            cwd=workspace_root,
            text=True,
            capture_output=True,
            check=False,
            timeout=_GIT_STATUS_TIMEOUT_SECONDS,
        )
    except (FileNotFoundError, TimeoutExpired):
        return WORKSPACE_STATE_UNAVAILABLE
    if completed.returncode != 0:
        return WORKSPACE_STATE_UNAVAILABLE
    if completed.stdout.strip():
        return WORKSPACE_STATE_DIRTY
    return WORKSPACE_STATE_CLEAN
