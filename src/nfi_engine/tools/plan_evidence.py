from __future__ import annotations

import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

EVIDENCE_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?:\.omo/evidence|evidence)/[A-Za-z0-9._/-]*[A-Za-z0-9_-]\.[A-Za-z0-9]+",
)
REQUIRED_ARG_COUNT: Final = 2
USAGE: Final = "usage: python3 scripts/verify_plan_evidence.py <plan.md> <evidence-dir>\n"


@dataclass(frozen=True, slots=True)
class EvidenceCheck:
    referenced: tuple[Path, ...]
    missing: tuple[Path, ...]


def collect_evidence_paths(plan_text: str) -> tuple[Path, ...]:
    seen: set[str] = set()
    paths: list[Path] = []
    for match in EVIDENCE_PATTERN.finditer(plan_text):
        raw_path = match.group(0)
        if raw_path in seen:
            continue
        seen.add(raw_path)
        paths.append(Path(raw_path))
    return tuple(paths)


def verify_plan_evidence(
    plan_path: Path,
    evidence_dir: Path,
    *,
    project_root: Path,
) -> EvidenceCheck:
    referenced = collect_evidence_paths(plan_path.read_text(encoding="utf-8"))
    missing: list[Path] = []
    for reference in referenced:
        candidate = _evidence_path(
            reference,
            evidence_dir=evidence_dir,
            project_root=project_root,
        )
        if not candidate.exists():
            missing.append(reference)
    return EvidenceCheck(referenced=referenced, missing=tuple(missing))


def format_evidence_report(result: EvidenceCheck) -> str:
    summary = f"referenced={len(result.referenced)} missing={len(result.missing)}"
    if not result.missing:
        return f"PLAN_EVIDENCE_OK {summary}\n"
    missing_lines = "\n".join(f"- {path.as_posix()}" for path in result.missing)
    return f"PLAN_EVIDENCE_MISSING {summary}\n{missing_lines}\n"


def main(argv: Sequence[str] | None = None) -> int:
    args = tuple(sys.argv[1:] if argv is None else argv)
    if len(args) != REQUIRED_ARG_COUNT:
        sys.stderr.write(USAGE)
        return 2
    plan_path = Path(args[0])
    evidence_dir = Path(args[1])
    result = verify_plan_evidence(plan_path, evidence_dir, project_root=Path.cwd())
    sys.stdout.write(format_evidence_report(result))
    if result.missing:
        return 1
    return 0


def _evidence_path(reference: Path, *, evidence_dir: Path, project_root: Path) -> Path:
    parts = reference.parts
    if parts[:2] == (".omo", "evidence"):
        return project_root.joinpath(*parts)
    if parts[:1] == ("evidence",):
        return evidence_dir.joinpath(*parts[1:])
    return project_root / reference


if __name__ == "__main__":
    raise SystemExit(main())
