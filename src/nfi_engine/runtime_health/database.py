from __future__ import annotations

import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from nfi_engine.persistence.session import SQLITE_ASYNC_PREFIX
from nfi_engine.runtime_health.models import RuntimeDatabaseSnapshot, RuntimeHealthState

MEMORY_SQLITE_URL: Final = f"{SQLITE_ASYNC_PREFIX}:memory:"


def collect_database_snapshot(
    *,
    database_url: str,
    now: datetime | None = None,
) -> RuntimeDatabaseSnapshot:
    captured_at = now if now is not None else datetime.now(UTC)
    if database_url == MEMORY_SQLITE_URL:
        return RuntimeDatabaseSnapshot(
            captured_at=captured_at,
            readable=True,
            writable=True,
            state=RuntimeHealthState.HEALTHY,
            message="database_url=sqlite_memory",
        )
    if not database_url.startswith(SQLITE_ASYNC_PREFIX):
        return RuntimeDatabaseSnapshot(
            captured_at=captured_at,
            readable=False,
            writable=False,
            state=RuntimeHealthState.DEGRADED,
            message="database_url=unsupported",
        )

    raw_path = database_url.removeprefix(SQLITE_ASYNC_PREFIX)
    path = Path(raw_path)
    target = path if path.exists() else _existing_parent(path.parent)
    readable = _can_read(target)
    writable = _can_write(target)
    state = RuntimeHealthState.HEALTHY if readable and writable else RuntimeHealthState.BLOCKED
    return RuntimeDatabaseSnapshot(
        captured_at=captured_at,
        readable=readable,
        writable=writable,
        state=state,
        message=f"database_path={path}",
    )


def _can_read(path: Path) -> bool:
    return path.exists() and os.access(path, os.R_OK)


def _can_write(path: Path) -> bool:
    return path.exists() and os.access(path, os.W_OK)


def _existing_parent(path: Path) -> Path:
    current = path
    while not current.exists() and current != current.parent:
        current = current.parent
    return current
