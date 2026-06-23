from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import Final

from nfi_engine.strategy.nfi_x7.metadata import X7_METADATA


@unique
class X7CoverageStatus(StrEnum):
    VERIFIED = "verified"
    PENDING = "pending"
    BLOCKED = "blocked"


@dataclass(frozen=True, slots=True)
class X7CoverageModule:
    name: str
    status: X7CoverageStatus
    evidence_path: str
    blocker: str | None = None


@dataclass(frozen=True, slots=True)
class X7CoverageReport:
    modules: tuple[X7CoverageModule, ...]

    @property
    def covered_modules(self) -> tuple[str, ...]:
        return tuple(
            module.name for module in self.modules if module.status is X7CoverageStatus.VERIFIED
        )

    @property
    def pending_modules(self) -> tuple[str, ...]:
        return tuple(
            module.name for module in self.modules if module.status is not X7CoverageStatus.VERIFIED
        )

    @property
    def is_full_semantic_coverage(self) -> bool:
        return len(self.pending_modules) == 0


TODO_01_EVIDENCE_PATH: Final = (
    ".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-01-provenance-coverage.md"
)
TODO_02_EVIDENCE_PATH: Final = (
    ".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-02-coverage-inspect.json"
)
TODO_06_EVIDENCE_PATH: Final = (
    ".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-06-feature-graph.json"
)
TARGET_MODULES: Final = (
    X7CoverageModule(
        name="metadata",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=X7_METADATA.provenance_evidence_path,
    ),
    X7CoverageModule(
        name="data_requirements",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=TODO_01_EVIDENCE_PATH,
    ),
    X7CoverageModule(
        name="strategy_callback_boundary",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=TODO_01_EVIDENCE_PATH,
    ),
    X7CoverageModule(
        name="semantic_coverage_ledger",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=TODO_02_EVIDENCE_PATH,
    ),
    X7CoverageModule(
        name="indicator_runtime",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-05-indicators-happy.json",
    ),
    X7CoverageModule(
        name="feature_graph",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=TODO_06_EVIDENCE_PATH,
    ),
    X7CoverageModule(
        name="entry_signals",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-07-entry-backtest.json",
    ),
    X7CoverageModule(
        name="exit_signals",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-08-exit-backtest.json",
    ),
    X7CoverageModule(
        name="stake_sizing",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-09-positioning-happy.txt",
    ),
    X7CoverageModule(
        name="protections",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-10-protections-happy.json",
    ),
    X7CoverageModule(
        name="runtime_integration",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-12-paper-timeline.json",
    ),
    X7CoverageModule(
        name="runtime_safety_gates",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-13-wallet-risk-http.txt",
    ),
    X7CoverageModule(
        name="operator_status_surface",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=(
            ".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-14-operator-status-proof.md"
        ),
    ),
    X7CoverageModule(
        name="performance_budget",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-15-benchmark.json",
    ),
    X7CoverageModule(
        name="release_docs",
        status=X7CoverageStatus.VERIFIED,
        evidence_path=".omo/evidence/2026-06-20-nfi-x7-semantic-port/task-16-install-docs-smoke.txt",
    ),
)


def build_x7_coverage_report(
    module_ledgers: tuple[X7CoverageModule, ...] = TARGET_MODULES,
    *,
    project_root: Path | None = None,
    require_evidence_artifacts: bool = True,
) -> X7CoverageReport:
    root = Path.cwd() if project_root is None else project_root
    return X7CoverageReport(
        modules=tuple(
            _with_evidence_gate(
                module=module,
                project_root=root,
                require_evidence_artifacts=require_evidence_artifacts,
            )
            for module in module_ledgers
        ),
    )


def worktree_evidence_available(project_root: Path | None = None) -> bool:
    root = Path.cwd() if project_root is None else project_root
    return (root / ".omo" / "evidence").exists()


def _with_evidence_gate(
    *,
    module: X7CoverageModule,
    project_root: Path,
    require_evidence_artifacts: bool,
) -> X7CoverageModule:
    if not require_evidence_artifacts:
        return module
    if module.status is not X7CoverageStatus.VERIFIED:
        return module
    evidence_path = project_root / module.evidence_path
    if evidence_path.exists():
        return module
    return X7CoverageModule(
        name=module.name,
        status=X7CoverageStatus.BLOCKED,
        evidence_path=module.evidence_path,
        blocker="Verified coverage module is missing its required evidence artifact.",
    )
