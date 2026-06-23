from __future__ import annotations

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FEATURE_DOC = PROJECT_ROOT / "docs" / "freqtrade-feature-coverage.md"
WORDING_SCAN = PROJECT_ROOT / "scripts" / "release_wording_scan.py"


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


def test_release_wording_scan_reports_zero_violations_for_public_docs() -> None:
    # Given: the deterministic release wording scanner.
    command = [sys.executable, str(WORDING_SCAN)]

    # When: public docs and README are scanned.
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then: blocked public claims are absent outside policy/negative contexts.
    assert result.returncode == 0, result.stdout + result.stderr
    assert "release_wording_scan=ok" in result.stdout
    assert "violations=0" in result.stdout


def test_release_wording_scan_rejects_unqualified_blocked_claim(tmp_path: Path) -> None:
    # Given: a controlled public wording violation.
    candidate = tmp_path / "bad-release.md"
    candidate.write_text(
        "NFI Engine is live-money ready with guaranteed profit.\n", encoding="utf-8"
    )

    # When: the candidate text is scanned.
    result = subprocess.run(
        [sys.executable, str(WORDING_SCAN), str(candidate)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then: the scanner reports the exact blocked phrasing class.
    assert result.returncode == 1
    assert "release_wording_scan=failed" in result.stdout
    assert "violations=2" in result.stdout
    assert "guaranteed profit" in result.stdout
    assert "live-money ready" in result.stdout


def test_release_wording_scan_rejects_unqualified_korean_claim(tmp_path: Path) -> None:
    # Given: a controlled Korean public wording violation.
    candidate = tmp_path / "bad-korean-release.md"
    candidate.write_text(
        "NFI Engine은 Freqtrade보다 우월하고 수익 보장입니다.\n",
        encoding="utf-8",
    )

    # When: the candidate text is scanned.
    result = subprocess.run(
        [sys.executable, str(WORDING_SCAN), str(candidate)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then: the scanner reports Korean superiority and profit claims.
    assert result.returncode == 1
    assert "release_wording_scan=failed" in result.stdout
    assert "violations=2" in result.stdout
    assert "Freqtrade superiority claim" in result.stdout
    assert "profit promise" in result.stdout
