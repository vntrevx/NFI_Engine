from __future__ import annotations

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parents[3]
README: Final = PROJECT_ROOT / "README.md"
DOCKER_DOC: Final = PROJECT_ROOT / "docs" / "docker.md"
UI_DOC: Final = PROJECT_ROOT / "docs" / "ui.md"
OPERATIONS_DOC: Final = PROJECT_ROOT / "docs" / "operations.md"
CONTRIBUTING_DOC: Final = PROJECT_ROOT / "docs" / "contributing.md"
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
        "login_token_file=.runtime/docker.env",
        "bash scripts/uninstall.sh --yes",
        "First Run",
    )

    # Then: it leads with the Docker installer instead of a manual dev flow.
    for fragment in required_fragments:
        assert fragment in quickstart
    assert "uv sync" not in quickstart
    assert "uv run nfi-engine serve" not in quickstart


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
