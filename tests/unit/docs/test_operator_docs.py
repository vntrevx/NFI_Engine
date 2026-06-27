from __future__ import annotations

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[3]
README: Final = PROJECT_ROOT / "README.md"
KOREAN_README: Final = PROJECT_ROOT / "README.ko.md"
DOCKER_DOC: Final = PROJECT_ROOT / "docs" / "docker.md"
UI_DOC: Final = PROJECT_ROOT / "docs" / "ui.md"
OPERATIONS_DOC: Final = PROJECT_ROOT / "docs" / "operations.md"
CONTRIBUTING_DOC: Final = PROJECT_ROOT / "docs" / "contributing.md"
QUALITY_GATE_SCRIPT: Final = PROJECT_ROOT / "scripts" / "quality_gate.sh"
ZERO_OCTET: Final = "0"
PUBLIC_BIND_LITERAL: Final = f"{ZERO_OCTET}.{ZERO_OCTET}.{ZERO_OCTET}.{ZERO_OCTET}"


def test_quickstart_is_one_command_first_run_path() -> None:
    # Given: the public README for a new operator.
    content = README.read_text(encoding="utf-8")
    quickstart = content.split("## Quickstart", maxsplit=1)[1].split("##", maxsplit=1)[0]

    # When: the primary quickstart section is inspected.
    required_fragments = (
        "bash scripts/install.sh --yes --paper --testnet",
        "http://127.0.0.1:18080/",
        "generated operator password from `.runtime/docker.env`",
        "bash scripts/uninstall.sh --yes",
        "First Run",
    )

    # Then: it leads with the Docker installer instead of a manual dev flow.
    for fragment in required_fragments:
        assert fragment in quickstart
    assert "uv sync" not in quickstart
    assert "uv run nfi-engine serve" not in quickstart


def test_readme_has_korean_operator_version_and_docs_gate() -> None:
    # Given: public README files and the docs quality gate.
    english = README.read_text(encoding="utf-8")
    korean = KOREAN_README.read_text(encoding="utf-8")
    script = QUALITY_GATE_SCRIPT.read_text(encoding="utf-8")

    # When: the public entrypoints are inspected.
    required_korean_fragments = (
        "paper/testnet RC",
        "bash scripts/install.sh --yes --paper --testnet",
        "실거래 주문 실행",
        "차단",
        "언어 선택",
        "README.md",
    )

    # Then: Korean operators get a maintained entrypoint with the same safety boundary.
    assert "[한국어](README.ko.md)" in english
    assert "[English](README.md)" in korean
    assert "README.ko.md" in script
    for fragment in required_korean_fragments:
        assert fragment in korean


def test_docs_explain_first_run_secrets_language_and_uninstall() -> None:
    # Given: the operator-facing docs.
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in (README, DOCKER_DOC, UI_DOC, OPERATIONS_DOC)
    )

    # When: setup, localization, and lifecycle guidance are inspected.
    required_fragments = (
        "write-only",
        "redacted",
        "Language Selector",
        "English, Korean, and Greek",
        "Safe Uninstall",
        "Destructive Purge",
        "support report",
        "benchmark evidence",
    )

    # Then: the docs explain the simple operator path without unsafe shortcuts.
    for fragment in required_fragments:
        assert fragment in combined
    assert "profit guaranteed" not in combined
    assert "safe live" not in combined
    assert PUBLIC_BIND_LITERAL not in combined
    assert "paste secret" not in combined


def test_contributor_docs_define_clean_room_and_feature_design_rules() -> None:
    # Given: contributor-facing public docs.
    content = CONTRIBUTING_DOC.read_text(encoding="utf-8")

    # When: the project rules are inspected.
    required_fragments = (
        "Clean-Room Contribution Rules",
        "Feature Design Rules",
        "Freqtrade is a behavior benchmark",
        "Do not copy FreqUI",
        "benchmark evidence",
        "module boundary",
    )

    # Then: contributors get the original-product constraints before coding.
    for fragment in required_fragments:
        assert fragment in content


def test_quality_budget_governance_is_documented_and_runnable() -> None:
    # Given: contributor docs, README, and the local quality gate script.
    contributing = CONTRIBUTING_DOC.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    script = QUALITY_GATE_SCRIPT.read_text(encoding="utf-8")

    # When: T17 quality governance text is inspected.
    required_doc_fragments = (
        "scripts/quality_gate.sh --docs-only",
        "scripts/quality_gate.sh --strict",
        "scripts/quality_gate.sh --coverage-only",
        "touched-code coverage",
        "250 pure LOC",
        "Performance Budget Review",
        "no repeated config parse",
        "no unbounded DB read",
        "no unbounded candle/frame materialization",
        "no UI payload growth without a cap",
        "no new dependency without size/startup justification",
    )
    required_script_fragments = (
        "--docs-only",
        "--strict",
        "--coverage-only",
        "NFI_ENGINE_COVERAGE_MIN",
        "uv run pytest",
        "--cov-fail-under",
    )

    # Then: the governance policy cannot silently disappear from docs or shell surface.
    for fragment in required_doc_fragments:
        assert fragment in contributing
    assert "bash scripts/quality_gate.sh --docs-only" in readme
    assert "coverage smoke" in readme
    for fragment in required_script_fragments:
        assert fragment in script
