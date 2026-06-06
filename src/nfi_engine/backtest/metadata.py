from __future__ import annotations

import hashlib
import inspect
import platform
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from nfi_engine import __version__
from nfi_engine.backtest.models import ReproducibilityMetadata, SimulatorScenarioMetadata
from nfi_engine.strategy import RequiredFreqtradeStrategy

PROJECT_ROOT: Final = Path(__file__).resolve().parents[3]
LOCKFILE_NAME: Final = "uv.lock"
GIT_SHA_LENGTH: Final = 40


@dataclass(frozen=True, slots=True)
class ReproducibilityMetadataRequest:
    config_path: Path
    candle_path: Path
    strategy: RequiredFreqtradeStrategy
    command_args: tuple[str, ...]
    simulator: SimulatorScenarioMetadata | None = None
    created_at: datetime | None = None
    project_root: Path = PROJECT_ROOT


def build_reproducibility_metadata(
    request: ReproducibilityMetadataRequest,
) -> ReproducibilityMetadata:
    return ReproducibilityMetadata(
        config_hash=sha256_file(request.config_path),
        strategy_hash=strategy_source_hash(request.strategy),
        data_hash=sha256_file(request.candle_path),
        engine_version=__version__,
        git_commit=current_git_commit(request.project_root),
        dependency_lock_hash=sha256_file(request.project_root / LOCKFILE_NAME),
        python_version=platform.python_version(),
        created_at=datetime.now(UTC) if request.created_at is None else request.created_at,
        command_args=request.command_args,
        simulator=request.simulator,
    )


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def strategy_source_hash(strategy: RequiredFreqtradeStrategy) -> str:
    strategy_type = type(strategy)
    source = _strategy_source(strategy_type)
    payload = f"{strategy_type.__module__}:{strategy_type.__qualname__}\n{source}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def current_git_commit(project_root: Path) -> str | None:
    try:
        git_dir = _git_dir(project_root)
        if git_dir is None:
            return None
        head = (git_dir / "HEAD").read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if head.startswith("ref: "):
        return _commit_from_ref(git_dir=git_dir, ref=head.removeprefix("ref: ").strip())
    if len(head) == GIT_SHA_LENGTH:
        return head
    return None


def _git_dir(project_root: Path) -> Path | None:
    git_path = project_root / ".git"
    if git_path.is_dir():
        return git_path
    content = git_path.read_text(encoding="utf-8").strip()
    if not content.startswith("gitdir: "):
        return None
    return (project_root / content.removeprefix("gitdir: ").strip()).resolve()


def _commit_from_ref(*, git_dir: Path, ref: str) -> str | None:
    ref_path = git_dir / ref
    if ref_path.exists():
        commit = ref_path.read_text(encoding="utf-8").strip()
        if len(commit) == GIT_SHA_LENGTH:
            return commit
        return None
    return _commit_from_packed_refs(git_dir=git_dir, ref=ref)


def _commit_from_packed_refs(*, git_dir: Path, ref: str) -> str | None:
    packed_refs = git_dir / "packed-refs"
    if not packed_refs.exists():
        return None
    for line in packed_refs.read_text(encoding="utf-8").splitlines():
        commit, separator, packed_ref = line.partition(" ")
        if separator == " " and packed_ref == ref and len(commit) == GIT_SHA_LENGTH:
            return commit
    return None


def _strategy_source(strategy_type: type[RequiredFreqtradeStrategy]) -> str:
    try:
        return inspect.getsource(strategy_type)
    except (OSError, TypeError):
        source_path = inspect.getsourcefile(strategy_type)
        if source_path is None:
            return ""
        path = Path(source_path)
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")
