from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from nfi_engine.tools.x7_provenance import (
    X7ProvenanceInputs,
    build_x7_provenance,
    main,
    render_markdown_report,
)

if TYPE_CHECKING:
    import pytest


def test_build_x7_provenance_extracts_public_structural_facts(tmp_path: Path) -> None:
    # Given
    source = _sample_x7_source()
    source_path = tmp_path / "NostalgiaForInfinityX7.py"
    source_path.write_text(source, encoding="utf-8")
    inputs = X7ProvenanceInputs(
        source_path=source_path,
        upstream_commit="abc123",
        source_url="https://example.invalid/NostalgiaForInfinityX7.py",
        observed_at="2026-06-20",
        output_path=tmp_path / "provenance.md",
    )

    # When
    provenance = build_x7_provenance(inputs)

    # Then
    assert provenance.raw_sha256 == hashlib.sha256(source.encode("utf-8")).hexdigest()
    assert provenance.strategy_class_name == "NostalgiaForInfinityX7"
    assert provenance.interface_version == 3
    assert provenance.strategy_version == "v17.4.258"
    assert provenance.base_timeframe == "5m"
    assert provenance.informative_timeframes == ("15m", "1h", "4h", "1d")
    assert provenance.import_roots == ("freqtrade", "pandas")
    assert provenance.method_names == ("version", "populate_indicators", "informative_pairs")


def test_render_markdown_report_avoids_source_code_bodies(tmp_path: Path) -> None:
    # Given
    source_path = tmp_path / "NostalgiaForInfinityX7.py"
    source_path.write_text(_sample_x7_source(), encoding="utf-8")
    inputs = X7ProvenanceInputs(
        source_path=source_path,
        upstream_commit="abc123",
        source_url="https://example.invalid/NostalgiaForInfinityX7.py",
        observed_at="2026-06-20",
        output_path=tmp_path / "provenance.md",
    )
    provenance = build_x7_provenance(inputs)

    # When
    report = render_markdown_report(provenance)

    # Then
    assert "method_count: `3`" in report
    assert "- `populate_indicators`" in report
    assert 'return "v17.4.258"' not in report
    assert "Upstream body intentionally excluded" not in report


def test_main_reports_missing_source_path(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Given
    output_path = tmp_path / "provenance.md"

    # When
    exit_code = main(
        (
            "--source",
            str(tmp_path / "missing.py"),
            "--commit",
            "abc123",
            "--source-url",
            "https://example.invalid/NostalgiaForInfinityX7.py",
            "--observed-at",
            "2026-06-20",
            "--output",
            str(output_path),
        ),
    )

    # Then
    captured = capsys.readouterr()
    assert exit_code == 1
    assert "X7_PROVENANCE_FILE_ERROR" in captured.err
    assert not output_path.exists()


def _sample_x7_source() -> str:
    return """\
import pandas
from freqtrade.strategy import IStrategy


class NostalgiaForInfinityX7(IStrategy):
    INTERFACE_VERSION = 3
    timeframe = "5m"

    def version(self) -> str:
        return "v17.4.258"

    def populate_indicators(self):
        return "Upstream body intentionally excluded"

    def informative_pairs(self):
        return [
            ("BTC/USDT", "15m"),
            ("BTC/USDT", "1h"),
            ("BTC/USDT", "4h"),
            ("BTC/USDT", "1d"),
        ]
"""
