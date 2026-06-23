from __future__ import annotations

import resource
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from nfi_engine.runtime_health.models import RuntimeHealthState, RuntimeResourceSnapshot

MIN_FREE_DISK_BYTES: Final = 128 * 1024 * 1024
WARN_RSS_BYTES: Final = 768 * 1024 * 1024


def collect_runtime_resources(
    *,
    path: Path | None = None,
    now: datetime | None = None,
) -> RuntimeResourceSnapshot:
    resolved_path = path if path is not None else Path()
    disk_usage = shutil.disk_usage(resolved_path)
    rss_bytes = _rss_bytes()
    return RuntimeResourceSnapshot(
        captured_at=now if now is not None else datetime.now(UTC),
        free_disk_bytes=disk_usage.free,
        memory_rss_bytes=rss_bytes,
        disk_state=(
            RuntimeHealthState.HEALTHY
            if disk_usage.free >= MIN_FREE_DISK_BYTES
            else RuntimeHealthState.BLOCKED
        ),
        memory_state=(
            RuntimeHealthState.HEALTHY
            if rss_bytes <= WARN_RSS_BYTES
            else RuntimeHealthState.DEGRADED
        ),
    )


def _rss_bytes() -> int:
    usage = resource.getrusage(resource.RUSAGE_SELF)
    return int(usage.ru_maxrss) * 1024
