#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[1]
DOCS_ROOT: Final = PROJECT_ROOT / "docs"
KOREAN_README: Final = PROJECT_ROOT / "README.ko.md"
RELEASE_WORDING_POLICY: Final = DOCS_ROOT / "release-wording.md"

ALLOW_CONTEXT_MARKERS: Final = (
    "no ",
    "not ",
    "without ",
    "must not",
    "do not",
    "never ",
    "blocked",
    "excluded",
    "out of scope",
    "requires",
    "cannot",
    "avoid",
    "release-critical",
    "negative",
    "negative probe",
    "forbidden wording",
    "차단",
    "아님",
    "아니다",
    "아직",
    "별도 승인",
    "금지",
    "미구현",
    "검토",
    "잡음",
    "증명된 건 아니다",
)
ALLOW_HEADINGS: Final = (
    "blocked phrasing",
    "excluded",
    "milestone 1 limits",
)


@dataclass(frozen=True, slots=True)
class BlockedPhrase:
    label: str
    triggers: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WordingViolation:
    path: Path
    line_number: int
    label: str
    line: str


BLOCKED_PHRASES: Final = (
    BlockedPhrase(label="guaranteed profit", triggers=("guaranteed profit",)),
    BlockedPhrase(
        label="profit promise",
        triggers=("profit promise", "profit promises", "수익 보장", "수익 약속"),
    ),
    BlockedPhrase(
        label="safety guarantee",
        triggers=("guaranteed safety", "safety guarantee", "안전 보장"),
    ),
    BlockedPhrase(
        label="profitability claim",
        triggers=("profitability claim", "profitability claims"),
    ),
    BlockedPhrase(
        label="full NFI X7 trade parity",
        triggers=(
            "full nfi x7 trade parity",
            "완전 nfi x7 거래 패리티",
            "완전한 nfi x7 거래 패리티",
        ),
    ),
    BlockedPhrase(label="full upstream NFI parity", triggers=("full upstream nfi parity",)),
    BlockedPhrase(label="100% parity", triggers=("100% parity", "완전 패리티")),
    BlockedPhrase(
        label="Freqtrade superiority claim",
        triggers=("better than freqtrade", "superior to freqtrade", "freqtrade보다 우월"),
    ),
    BlockedPhrase(
        label="live-money ready",
        triggers=("live-money ready", "live money ready", "실거래 준비 완료"),
    ),
    BlockedPhrase(label="100% complete", triggers=("100% complete", "100% 완료")),
    BlockedPhrase(
        label="Pi4 public performance claim",
        triggers=(
            "pi4 public performance claim",
            "pi4 public performance claims",
            "pi4 속도 우위",
            "raspberry pi 4 speed superiority",
        ),
    ),
)


def main(argv: tuple[str, ...]) -> int:
    paths = tuple(Path(argument) for argument in argv) if len(argv) > 0 else _default_paths()
    violations = tuple(violation for path in paths for violation in _scan_file(path))
    if len(violations) == 0:
        sys.stdout.write("release_wording_scan=ok\n")
        sys.stdout.write(f"scanned_files={len(paths)}\n")
        sys.stdout.write("violations=0\n")
        return 0
    sys.stdout.write("release_wording_scan=failed\n")
    sys.stdout.write(f"scanned_files={len(paths)}\n")
    sys.stdout.write(f"violations={len(violations)}\n")
    for violation in violations:
        path = _display_path(violation.path)
        line_number = violation.line_number
        label = violation.label
        line = violation.line
        sys.stdout.write(f"violation={path}:{line_number}:{label}:{line}\n")
    return 1


def _default_paths() -> tuple[Path, ...]:
    docs = tuple(sorted(DOCS_ROOT.glob("*.md")))
    return (PROJECT_ROOT / "README.md", KOREAN_README, *docs)


def _scan_file(path: Path) -> tuple[WordingViolation, ...]:
    heading = ""
    violations: list[WordingViolation] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped_line = raw_line.strip()
        if stripped_line.startswith("#"):
            heading = stripped_line.lstrip("#").strip().lower()
        line = stripped_line.lower()
        violations.extend(
            WordingViolation(
                path=path,
                line_number=line_number,
                label=phrase.label,
                line=stripped_line,
            )
            for phrase in BLOCKED_PHRASES
            if _contains_trigger(line=line, phrase=phrase)
            and not _allowed_context(
                path=path,
                heading=heading,
                line=line,
            )
        )
    return tuple(violations)


def _contains_trigger(*, line: str, phrase: BlockedPhrase) -> bool:
    return any(trigger in line for trigger in phrase.triggers)


def _allowed_context(*, path: Path, heading: str, line: str) -> bool:
    if path.resolve() == RELEASE_WORDING_POLICY.resolve():
        return True
    if any(allowed_heading in heading for allowed_heading in ALLOW_HEADINGS):
        return True
    return any(marker in line for marker in ALLOW_CONTEXT_MARKERS)


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return str(resolved.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


if __name__ == "__main__":
    raise SystemExit(main(tuple(sys.argv[1:])))
