from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FEATURE_DOC = PROJECT_ROOT / "docs" / "freqtrade-feature-coverage.md"


def test_feature_coverage_matrix_documents_clean_room_differentiation() -> None:
    # Given: the M2 feature coverage document.
    content = FEATURE_DOC.read_text(encoding="utf-8")

    # When: the coverage matrix is inspected as a public planning contract.
    required_fragments = (
        "NFI Engine angle",
        "operator-usability",
        "performance",
        "safety",
        "strategy-research",
        "plugin-ecosystem",
        "oss-polish",
        "Clean-Room Boundary",
    )

    # Then: it documents feature coverage without copycat positioning.
    for fragment in required_fragments:
        assert fragment in content
    assert "copy FreqUI" not in content
    assert "full Freqtrade parity" not in content


def test_feature_coverage_matrix_lists_representative_freqtrade_categories() -> None:
    # Given: the M2 feature coverage document.
    content = FEATURE_DOC.read_text(encoding="utf-8")

    # When: the functional benchmark categories are inspected.
    categories = (
        "Setup",
        "Configuration",
        "Bot control",
        "REST API",
        "Logs",
        "Trades",
        "Pairlists",
        "Backtesting",
        "Charts",
        "Hyperopt",
        "FreqAI",
        "Notifications",
        "Futures",
        "Strategy callbacks",
        "Persistence",
        "Backup",
    )

    # Then: the matrix covers the broad feature ideas as a roadmap.
    for category in categories:
        assert category in content
