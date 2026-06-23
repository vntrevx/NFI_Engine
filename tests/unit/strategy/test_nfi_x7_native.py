from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from nfi_engine.domain import (
    Leverage,
    OrderId,
    PositionSide,
    StakeAmount,
    TradeId,
    TradingMode,
    TradingPair,
)
from nfi_engine.strategy import (
    FreqtradeStrategyAdapter,
    RunMode,
    StrategyFeatureName,
    StrategyFrame,
    StrategyMetadata,
    StrategyOrder,
    StrategyRow,
    StrategyTrade,
)
from nfi_engine.strategy.nfi_x7 import (
    LONG_ENTRY_TAG,
    X7_DATA_REQUIREMENTS,
    X7_METADATA,
    X7CoverageModule,
    X7CoverageStatus,
    X7NativeStrategy,
    build_x7_coverage_report,
)


def test_native_x7_metadata_and_data_requirements_are_engine_owned() -> None:
    # Given
    metadata = X7_METADATA
    requirements = X7_DATA_REQUIREMENTS

    # When
    coverage = build_x7_coverage_report()

    # Then
    assert metadata.name == "NFI_X7_NATIVE"
    assert metadata.strategy_class_name == "X7NativeStrategy"
    assert metadata.observed_upstream_version == "v17.4.258"
    assert metadata.base_timeframe == "5m"
    assert requirements.base_timeframe == "5m"
    assert requirements.informative_timeframes == ("15m", "1h", "4h", "1d")
    assert requirements.mandatory_external_dependencies == ()
    assert coverage.is_full_semantic_coverage is True
    assert coverage.pending_modules == ()
    assert "metadata" in coverage.covered_modules
    assert "indicator_runtime" in coverage.covered_modules
    assert "feature_graph" in coverage.covered_modules
    assert "entry_signals" in coverage.covered_modules
    assert "exit_signals" in coverage.covered_modules
    assert "stake_sizing" in coverage.covered_modules
    assert "protections" in coverage.covered_modules
    assert "release_docs" in coverage.covered_modules
    assert coverage.modules[0].status is X7CoverageStatus.VERIFIED
    assert coverage.modules[0].evidence_path.endswith("task-01-provenance-coverage.md")


def test_native_x7_coverage_blocks_verified_module_when_evidence_is_missing(
    tmp_path: Path,
) -> None:
    # Given
    modules = (
        X7CoverageModule(
            name="metadata",
            status=X7CoverageStatus.VERIFIED,
            evidence_path=".omo/evidence/missing.md",
        ),
    )

    # When
    coverage = build_x7_coverage_report(
        modules,
        project_root=tmp_path,
        require_evidence_artifacts=True,
    )

    # Then
    assert coverage.is_full_semantic_coverage is False
    assert coverage.covered_modules == ()
    assert coverage.pending_modules == ("metadata",)
    assert coverage.modules[0].status is X7CoverageStatus.BLOCKED
    assert coverage.modules[0].blocker == (
        "Verified coverage module is missing its required evidence artifact."
    )


def test_native_x7_coverage_uses_packaged_manifest_when_evidence_gate_is_disabled(
    tmp_path: Path,
) -> None:
    modules = (
        X7CoverageModule(
            name="metadata",
            status=X7CoverageStatus.VERIFIED,
            evidence_path=".omo/evidence/missing.md",
        ),
    )

    coverage = build_x7_coverage_report(
        modules,
        project_root=tmp_path,
        require_evidence_artifacts=False,
    )

    assert coverage.is_full_semantic_coverage is True
    assert coverage.covered_modules == ("metadata",)
    assert coverage.pending_modules == ()
    assert coverage.modules[0].status is X7CoverageStatus.VERIFIED
    assert coverage.modules[0].blocker is None


def test_native_x7_coverage_default_ignores_incidental_worktree_evidence(
    tmp_path: Path,
) -> None:
    # Given
    (tmp_path / ".omo" / "evidence").mkdir(parents=True)
    modules = (
        X7CoverageModule(
            name="metadata",
            status=X7CoverageStatus.VERIFIED,
            evidence_path=".omo/evidence/missing.md",
        ),
    )

    # When
    coverage = build_x7_coverage_report(modules, project_root=tmp_path)

    # Then
    assert coverage.is_full_semantic_coverage is True
    assert coverage.covered_modules == ("metadata",)
    assert coverage.pending_modules == ()
    assert coverage.modules[0].status is X7CoverageStatus.VERIFIED


def test_native_x7_coverage_can_only_be_full_when_all_modules_are_verified_with_evidence(
    tmp_path: Path,
) -> None:
    # Given
    evidence_path = tmp_path / ".omo" / "evidence" / "complete.md"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text("ok\n", encoding="utf-8")
    modules = (
        X7CoverageModule(
            name="metadata",
            status=X7CoverageStatus.VERIFIED,
            evidence_path=".omo/evidence/complete.md",
        ),
        X7CoverageModule(
            name="runtime_integration",
            status=X7CoverageStatus.VERIFIED,
            evidence_path=".omo/evidence/complete.md",
        ),
    )

    # When
    coverage = build_x7_coverage_report(
        modules,
        project_root=tmp_path,
        require_evidence_artifacts=True,
    )

    # Then
    assert coverage.is_full_semantic_coverage is True
    assert coverage.covered_modules == ("metadata", "runtime_integration")
    assert coverage.pending_modules == ()


def test_native_x7_strategy_contract_is_selectable_by_existing_adapter() -> None:
    # Given
    strategy = X7NativeStrategy()
    adapter = FreqtradeStrategyAdapter.from_strategy(strategy)

    # When
    inspection = adapter.inspect()

    # Then
    assert inspection.name == "X7NativeStrategy"
    assert inspection.can_short is True
    assert inspection.timeframe == "5m"
    assert set(inspection.detected_callbacks) >= {
        "populate_indicators",
        "populate_entry_trend",
        "populate_exit_trend",
        "informative_pairs",
        "custom_exit",
        "custom_stake_amount",
        "order_filled",
        "adjust_trade_position",
        "confirm_trade_entry",
        "confirm_trade_exit",
        "bot_loop_start",
        "leverage",
    }


def test_native_x7_strategy_methods_build_features_and_entry_signals() -> None:
    # Given
    strategy = X7NativeStrategy()
    frame = _frame()
    metadata = _metadata()
    pair = metadata.pair
    stake = StakeAmount(Decimal(25))
    trade = StrategyTrade(trade_id=TradeId("trade-1"), pair=pair, side=PositionSide.LONG)
    order = StrategyOrder(order_id=OrderId("order-1"), pair=pair, side=PositionSide.LONG)

    # When
    indicator_frame = strategy.populate_indicators(frame, metadata)
    entry_frame = strategy.populate_entry_trend(indicator_frame, metadata)
    exit_frame = strategy.populate_exit_trend(entry_frame, metadata)
    informative_pairs = strategy.informative_pairs()
    custom_exit = strategy.custom_exit(trade)
    custom_stake = strategy.custom_stake_amount(pair, stake)
    leverage = strategy.leverage(pair, Leverage.one())
    strategy.order_filled(order, trade)
    position_adjustment = strategy.adjust_trade_position(trade)
    strategy.bot_loop_start()

    # Then
    assert indicator_frame.last_visible_row().feature(StrategyFeatureName("x7_base_roc_1")) > 0
    assert entry_frame.last_visible_row().enter_long is True
    assert entry_frame.last_visible_row().enter_tag == LONG_ENTRY_TAG
    assert exit_frame is entry_frame
    assert informative_pairs == (
        ("BTC/USDT:USDT", "15m"),
        ("BTC/USDT:USDT", "1h"),
        ("BTC/USDT:USDT", "4h"),
        ("BTC/USDT:USDT", "1d"),
    )
    assert custom_exit is None
    assert custom_stake == stake
    assert leverage.value == Decimal(3)
    assert position_adjustment is None


def _metadata() -> StrategyMetadata:
    return StrategyMetadata(
        pair=TradingPair.parse("ETH/USDT:USDT", TradingMode.FUTURES),
        timeframe="5m",
        runmode=RunMode.BACKTEST,
    )


def _frame() -> StrategyFrame:
    return StrategyFrame(
        rows=(
            StrategyRow(date="2026-01-01T00:00:00Z", close=Decimal(10)),
            StrategyRow(date="2026-01-01T00:05:00Z", close=Decimal(11)),
        ),
    )
