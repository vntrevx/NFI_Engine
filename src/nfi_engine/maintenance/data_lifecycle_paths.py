from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Final
from urllib.parse import urlsplit, urlunsplit

from nfi_engine.config import RuntimeSettings
from nfi_engine.events import REDACTED_TEXT
from nfi_engine.maintenance.data_lifecycle_types import (
    DataLifecycleCategoryFootprint,
    DataLifecycleCategoryName,
    DataLifecycleFile,
    DataLifecycleItemStatus,
    DataLifecycleRoots,
)

SQLITE_PREFIX: Final = "sqlite+aiosqlite:///"
SCAN_CATEGORY_ITEM_LIMIT: Final = 500
SCAN_TRUNCATED_REASON: Final = "scan_truncated"


def build_lifecycle_roots(
    *,
    settings: RuntimeSettings,
    workspace_root: Path,
) -> DataLifecycleRoots:
    sqlite = sqlite_path(settings.database.url, workspace_root=workspace_root)
    runtime = workspace_root / "data" if sqlite is None else sqlite.parent
    evidence = path_from_text(
        settings.notifications.jsonl_path,
        workspace_root=workspace_root,
    ).parent
    return DataLifecycleRoots(
        sqlite=sqlite,
        runtime=runtime,
        logs=runtime / "logs",
        backups=runtime / "backups",
        support_bundles=runtime / "support-bundles",
        evidence=evidence,
    )


def scan_lifecycle_categories(
    *,
    roots: DataLifecycleRoots,
) -> tuple[DataLifecycleCategoryFootprint, ...]:
    return (
        sqlite_category(roots),
        scan_category(DataLifecycleCategoryName.LOGS, roots.logs, roots.runtime),
        scan_category(DataLifecycleCategoryName.BACKUPS, roots.backups, roots.runtime),
        scan_category(
            DataLifecycleCategoryName.SUPPORT_BUNDLES,
            roots.support_bundles,
            roots.runtime,
        ),
        scan_category(DataLifecycleCategoryName.EVIDENCE, roots.evidence, roots.runtime),
    )


def sqlite_category(roots: DataLifecycleRoots) -> DataLifecycleCategoryFootprint:
    root = roots.runtime
    if roots.sqlite is None:
        return category(DataLifecycleCategoryName.SQLITE, root, ())
    items = tuple(
        existing_file_item(DataLifecycleCategoryName.SQLITE, path, root, protected=True)
        for path in (roots.sqlite, Path(f"{roots.sqlite}-wal"), Path(f"{roots.sqlite}-shm"))
        if path.exists()
    )
    missing = (
        ()
        if items
        else (
            DataLifecycleFile(
                category=DataLifecycleCategoryName.SQLITE,
                path=str(roots.sqlite),
                size_bytes=0,
                modified_at=None,
                status=DataLifecycleItemStatus.MISSING,
                reason="sqlite_missing",
            ),
        )
    )
    return category(DataLifecycleCategoryName.SQLITE, root, items + missing)


def scan_category(
    name: DataLifecycleCategoryName,
    root: Path,
    allowed_root: Path,
) -> DataLifecycleCategoryFootprint:
    if not root.exists():
        return category(name, root, ())
    items: list[DataLifecycleFile] = []
    truncated = False
    for path in root.rglob("*"):
        if not path.is_file() and not path.is_symlink():
            continue
        if len(items) >= SCAN_CATEGORY_ITEM_LIMIT:
            truncated = True
            break
        items.append(existing_file_item(name, path, allowed_root, protected=False))
    if truncated:
        items.append(scan_truncated_item(name, root))
    return category(name, root, tuple(items))


def scan_truncated_item(
    category_name: DataLifecycleCategoryName,
    root: Path,
) -> DataLifecycleFile:
    return DataLifecycleFile(
        category=category_name,
        path=str(root),
        size_bytes=0,
        modified_at=None,
        status=DataLifecycleItemStatus.SKIPPED,
        reason=SCAN_TRUNCATED_REASON,
    )


def existing_file_item(
    category_name: DataLifecycleCategoryName,
    path: Path,
    allowed_root: Path,
    *,
    protected: bool,
) -> DataLifecycleFile:
    resolved = path.resolve(strict=False)
    if not resolved.is_relative_to(allowed_root.resolve(strict=False)):
        return DataLifecycleFile(
            category=category_name,
            path=str(path),
            size_bytes=0,
            modified_at=None,
            status=DataLifecycleItemStatus.PROTECTED,
            reason="unsafe_path",
        )
    try:
        stat = path.stat()
    except OSError:
        return DataLifecycleFile(
            category=category_name,
            path=str(path),
            size_bytes=0,
            modified_at=None,
            status=DataLifecycleItemStatus.SKIPPED,
            reason="stat_failed",
        )
    return DataLifecycleFile(
        category=category_name,
        path=str(path),
        size_bytes=stat.st_size,
        modified_at=datetime.fromtimestamp(stat.st_mtime, UTC),
        status=DataLifecycleItemStatus.PROTECTED if protected else DataLifecycleItemStatus.SKIPPED,
        reason="protected_runtime_data" if protected else "retention_not_evaluated",
    )


def category(
    name: DataLifecycleCategoryName,
    root: Path,
    items: tuple[DataLifecycleFile, ...],
) -> DataLifecycleCategoryFootprint:
    return DataLifecycleCategoryFootprint(
        name=name,
        root=str(root),
        file_count=sum(
            1
            for item in items
            if item.status is not DataLifecycleItemStatus.MISSING
            and item.reason != SCAN_TRUNCATED_REASON
        ),
        total_bytes=sum(item.size_bytes for item in items),
        items=items,
    )


def sqlite_path(database_url: str, *, workspace_root: Path) -> Path | None:
    if not database_url.startswith(SQLITE_PREFIX):
        return None
    path_text = database_url.removeprefix(SQLITE_PREFIX)
    if path_text in {"", ":memory:"}:
        return None
    return path_from_text(path_text, workspace_root=workspace_root)


def path_from_text(path_text: str, *, workspace_root: Path) -> Path:
    path = Path(path_text)
    if path.is_absolute():
        return path
    return workspace_root / path


def redacted_database_url(database_url: str) -> str:
    if database_url.startswith(SQLITE_PREFIX):
        return database_url
    parsed = urlsplit(database_url)
    if parsed.scheme == "":
        return database_url
    netloc = parsed.netloc
    if "@" in netloc:
        _, host = netloc.rsplit("@", maxsplit=1)
        netloc = f"{REDACTED_TEXT}@{host}"
    query = REDACTED_TEXT if parsed.query else ""
    return urlunsplit((parsed.scheme, netloc, parsed.path, query, ""))
