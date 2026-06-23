from __future__ import annotations

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]
PURE_LOC_LIMIT: Final = 250
X7_LIVE_BOUNDARY_ROOTS: Final = (
    Path("src/nfi_engine/strategy/nfi_x7"),
    Path("src/nfi_engine/paper"),
    Path("src/nfi_engine/exchange"),
    Path("src/nfi_engine/preflight"),
    Path("src/nfi_engine/runtime_control"),
    Path("src/nfi_engine/runtime_health"),
    Path("src/nfi_engine/wallet"),
)


def test_x7_live_modules_stay_below_split_pressure() -> None:
    # Given: the X7/live-readiness runtime package boundaries.
    python_files = tuple(
        path for root in X7_LIVE_BOUNDARY_ROOTS for path in (PROJECT_ROOT / root).rglob("*.py")
    )

    # When: their pure LOC is measured without blank lines or comments.
    oversized = tuple(
        (path.relative_to(PROJECT_ROOT), pure_loc(path))
        for path in python_files
        if pure_loc(path) > PURE_LOC_LIMIT
    )

    # Then: no file crosses the module split-pressure ceiling.
    assert oversized == ()


def pure_loc(path: Path) -> int:
    return sum(
        1
        for line in path.read_text(encoding="utf-8").splitlines()
        if (stripped := line.strip()) and not stripped.startswith("#")
    )
