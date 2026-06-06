from __future__ import annotations

from pathlib import Path

from nfi_engine.reconciliation import (
    ReconciliationCode,
    load_reconciliation_fixture,
    reconcile_snapshot,
    startup_recovery_report,
)


def test_matching_snapshot_reports_zero_mismatches() -> None:
    # Given: local and exchange snapshots with identical safety state.
    snapshot = load_reconciliation_fixture(Path("tests/fixtures/exchange/reconcile_match.json"))

    # When: reconciliation runs in dry-run mode.
    report = reconcile_snapshot(snapshot=snapshot, dry_run=True)

    # Then: trading remains unblocked and no actions are suggested.
    assert report.apply is False
    assert report.trading_halted is False
    assert report.mismatch_count == 0
    assert report.issues == ()


def test_mismatch_snapshot_reports_all_recovery_codes() -> None:
    # Given: a fixture with local/exchange drift across orders, positions, balances, and locks.
    snapshot = load_reconciliation_fixture(
        Path("tests/fixtures/exchange/reconcile_mismatch.json"),
    )

    # When: reconciliation builds a dry-run report.
    report = reconcile_snapshot(snapshot=snapshot, dry_run=True)

    # Then: every safety-affecting drift is visible with dry-run suggestions.
    codes = {issue.code for issue in report.issues}
    assert ReconciliationCode.ORPHAN_LOCAL_ORDER in codes
    assert ReconciliationCode.ORPHAN_EXCHANGE_ORDER in codes
    assert ReconciliationCode.POSITION_MISMATCH in codes
    assert ReconciliationCode.BALANCE_MISMATCH in codes
    assert ReconciliationCode.LEVERAGE_MISMATCH in codes
    assert ReconciliationCode.MARGIN_MODE_MISMATCH in codes
    assert ReconciliationCode.STALE_LOCK in codes
    assert ReconciliationCode.DUPLICATE_LOCAL_TRADE in codes
    assert ReconciliationCode.MISSING_EXCHANGE_FILL in codes
    assert ReconciliationCode.PENDING_CANCEL in codes
    assert report.trading_halted is True
    assert all(issue.suggested_action.startswith("dry-run:") for issue in report.issues)


def test_startup_recovery_blocks_unsafe_run_when_drift_exists() -> None:
    # Given: startup recovery receives an unsafe mismatch snapshot.
    snapshot = load_reconciliation_fixture(
        Path("tests/fixtures/exchange/reconcile_mismatch.json"),
    )

    # When: startup recovery is evaluated.
    report = startup_recovery_report(snapshot=snapshot)

    # Then: startup is blocked before the paper engine can continue.
    assert report.trading_halted is True
    assert report.mismatch_count > 0
