from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import Path
from typing import Final

from nfi_engine.backtest import ReproducibilityMetadata
from nfi_engine.backtest.metadata import (
    ReproducibilityMetadataRequest,
    build_reproducibility_metadata,
)
from tests.fixtures.strategies.backtest_cases import LongExitStrategy, NoSignalStrategy

PROJECT_ROOT: Final = Path(__file__).resolve().parents[3]
CONFIG_PATH: Final = PROJECT_ROOT / "examples/spot-paper.yaml"
DATA_PATH: Final = PROJECT_ROOT / "tests/fixtures/candles/btc_usdt_5m.jsonl"
CREATED_AT: Final = datetime(2026, 1, 1, tzinfo=UTC)


def test_metadata_hashes_config_strategy_data_and_lockfile() -> None:
    # Given: a concrete config, data file, strategy object, and command arguments.
    strategy = LongExitStrategy()

    # When: reproducibility metadata is built.
    metadata = build_reproducibility_metadata(
        ReproducibilityMetadataRequest(
            config_path=CONFIG_PATH,
            candle_path=DATA_PATH,
            strategy=strategy,
            command_args=("backtest", "--config", str(CONFIG_PATH)),
            created_at=CREATED_AT,
            project_root=PROJECT_ROOT,
        ),
    )

    # Then: required hashes and runtime identifiers are present.
    assert metadata.config_hash == _sha256_file(CONFIG_PATH)
    assert metadata.data_hash == _sha256_file(DATA_PATH)
    assert metadata.dependency_lock_hash == _sha256_file(PROJECT_ROOT / "uv.lock")
    assert metadata.strategy_hash != ""
    assert metadata.engine_version == "0.1.0"
    assert metadata.created_at == CREATED_AT
    assert metadata.command_args == ("backtest", "--config", str(CONFIG_PATH))


def test_metadata_config_hash_changes_when_config_file_changes(tmp_path: Path) -> None:
    # Given: two config files with different risk values.
    changed_config = tmp_path / "changed.yaml"
    changed_config.write_text(
        CONFIG_PATH.read_text(encoding="utf-8").replace('stake_usdt: "10"', 'stake_usdt: "11"'),
        encoding="utf-8",
    )

    # When: metadata is built for each config.
    baseline = _metadata_for_config(CONFIG_PATH)
    changed = _metadata_for_config(changed_config)

    # Then: config_hash changes while the data hash remains stable.
    assert baseline.config_hash != changed.config_hash
    assert baseline.data_hash == changed.data_hash


def test_metadata_data_hash_changes_when_candle_file_changes(tmp_path: Path) -> None:
    # Given: two candle files with different closing prices.
    changed_data = tmp_path / "changed.jsonl"
    changed_data.write_text(
        DATA_PATH.read_text(encoding="utf-8").replace('"close":"102"', '"close":"103"', 1),
        encoding="utf-8",
    )

    # When: metadata is built for each data file.
    baseline = _metadata_for_data(DATA_PATH)
    changed = _metadata_for_data(changed_data)

    # Then: data_hash changes while the config hash remains stable.
    assert baseline.data_hash != changed.data_hash
    assert baseline.config_hash == changed.config_hash


def test_metadata_strategy_hash_changes_when_strategy_source_changes() -> None:
    # Given: two different strategy classes.
    first_strategy = NoSignalStrategy()
    second_strategy = LongExitStrategy()

    # When: metadata is built for each strategy.
    first = build_reproducibility_metadata(
        ReproducibilityMetadataRequest(
            config_path=CONFIG_PATH,
            candle_path=DATA_PATH,
            strategy=first_strategy,
            command_args=("backtest",),
            created_at=CREATED_AT,
            project_root=PROJECT_ROOT,
        ),
    )
    second = build_reproducibility_metadata(
        ReproducibilityMetadataRequest(
            config_path=CONFIG_PATH,
            candle_path=DATA_PATH,
            strategy=second_strategy,
            command_args=("backtest",),
            created_at=CREATED_AT,
            project_root=PROJECT_ROOT,
        ),
    )

    # Then: strategy_hash identifies the strategy implementation.
    assert first.strategy_hash != second.strategy_hash


def _metadata_for_config(config_path: Path) -> ReproducibilityMetadata:
    return build_reproducibility_metadata(
        ReproducibilityMetadataRequest(
            config_path=config_path,
            candle_path=DATA_PATH,
            strategy=LongExitStrategy(),
            command_args=("backtest",),
            created_at=CREATED_AT,
            project_root=PROJECT_ROOT,
        ),
    )


def _metadata_for_data(data_path: Path) -> ReproducibilityMetadata:
    return build_reproducibility_metadata(
        ReproducibilityMetadataRequest(
            config_path=CONFIG_PATH,
            candle_path=data_path,
            strategy=LongExitStrategy(),
            command_args=("backtest",),
            created_at=CREATED_AT,
            project_root=PROJECT_ROOT,
        ),
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
