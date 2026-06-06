from __future__ import annotations

from pathlib import Path

from nfi_engine.tools.plan_evidence import (
    collect_evidence_paths,
    format_evidence_report,
    verify_plan_evidence,
)


def test_collect_evidence_paths_deduplicates_references() -> None:
    # Given: plan text with repeated evidence references.
    plan_text = (
        "Evidence: `.omo/evidence/final-a.txt`, .omo/evidence/final-b.json\n"
        "Again: .omo/evidence/final-a.txt"
    )

    # When: evidence paths are collected.
    paths = collect_evidence_paths(plan_text)

    # Then: paths are returned once in first-seen order.
    assert paths == (
        Path(".omo/evidence/final-a.txt"),
        Path(".omo/evidence/final-b.json"),
    )


def test_collect_evidence_paths_ignores_prefix_examples() -> None:
    # Given: plan prose that mentions evidence filename prefixes.
    plan_text = "Evidence uses .omo/evidence/task- and .omo/evidence/final-* prefixes."

    # When: evidence paths are collected.
    paths = collect_evidence_paths(plan_text)

    # Then: incomplete prefixes are not treated as required files.
    assert paths == ()


def test_verify_plan_evidence_reports_missing_files(tmp_path: Path) -> None:
    # Given: a plan that references one present and one missing evidence file.
    evidence_dir = tmp_path / ".omo" / "evidence"
    evidence_dir.mkdir(parents=True)
    present = evidence_dir / "final-present.txt"
    present.write_text("ok\n", encoding="utf-8")
    plan = tmp_path / "plan.md"
    plan.write_text(
        "Evidence: .omo/evidence/final-present.txt, .omo/evidence/final-missing.txt\n",
        encoding="utf-8",
    )

    # When: the plan is checked against the evidence directory.
    result = verify_plan_evidence(plan, evidence_dir, project_root=tmp_path)

    # Then: only the absent evidence file is reported.
    assert result.missing == (Path(".omo/evidence/final-missing.txt"),)
    assert result.referenced == (
        Path(".omo/evidence/final-present.txt"),
        Path(".omo/evidence/final-missing.txt"),
    )


def test_format_evidence_report_prints_stable_summary(tmp_path: Path) -> None:
    # Given: a plan with one existing evidence artifact.
    evidence_dir = tmp_path / ".omo" / "evidence"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "final-ok.txt").write_text("ok\n", encoding="utf-8")
    plan = tmp_path / "plan.md"
    plan.write_text("Evidence: .omo/evidence/final-ok.txt\n", encoding="utf-8")
    result = verify_plan_evidence(plan, evidence_dir, project_root=tmp_path)

    # When: the result is formatted for a final audit artifact.
    report = format_evidence_report(result)

    # Then: the report has deterministic status and count fields.
    assert report == "PLAN_EVIDENCE_OK referenced=1 missing=0\n"
