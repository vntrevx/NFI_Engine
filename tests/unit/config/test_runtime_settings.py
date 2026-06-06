from __future__ import annotations

from pathlib import Path

import pytest

from nfi_engine.config import (
    ConfigErrorCode,
    ConfigLoadError,
    FieldMetadata,
    frontend_metadata,
    load_runtime_settings,
)
from nfi_engine.domain import TradingMode


def test_spot_paper_config_loads_when_live_trading_is_not_enabled(tmp_path: Path) -> None:
    # Given
    config_path = _write_config(
        tmp_path,
        (
            "exchange:",
            "  trading_mode: spot",
            "risk:",
            '  stake_usdt: "10"',
        ),
    )

    # When
    settings = load_runtime_settings(config_path)

    # Then
    assert settings.exchange.trading_mode is TradingMode.SPOT
    assert settings.engine.live_trading is False
    assert settings.risk.stake_usdt == 10


def test_unknown_config_key_is_rejected_when_yaml_contains_extra_field(tmp_path: Path) -> None:
    # Given
    config_path = _write_config(
        tmp_path,
        (
            "exchange:",
            "  trading_mode: spot",
            "unknown_section:",
            "  enabled: true",
        ),
    )

    # When
    with pytest.raises(ConfigLoadError) as exc_info:
        load_runtime_settings(config_path)

    # Then
    assert exc_info.value.code is ConfigErrorCode.CONFIG_VALIDATION_FAILED
    assert "extra_forbidden" in exc_info.value.message


def test_live_trading_without_confirmation_is_rejected(tmp_path: Path) -> None:
    # Given
    config_path = _write_config(
        tmp_path,
        (
            "engine:",
            "  live_trading: true",
            "exchange:",
            "  trading_mode: spot",
        ),
    )

    # When
    with pytest.raises(ConfigLoadError) as exc_info:
        load_runtime_settings(config_path)

    # Then
    assert exc_info.value.code is ConfigErrorCode.LIVE_TRADING_REQUIRES_CONFIRMATION


def test_live_trading_without_exchange_keys_is_rejected_when_confirmed(tmp_path: Path) -> None:
    # Given
    config_path = _write_config(
        tmp_path,
        (
            "engine:",
            "  live_trading: true",
            "  live_trading_confirmed: true",
            "exchange:",
            "  name: bybit",
            "  trading_mode: futures",
            "  margin_mode: isolated",
            "  testnet: true",
        ),
    )

    # When
    with pytest.raises(ConfigLoadError) as exc_info:
        load_runtime_settings(config_path)

    # Then
    assert exc_info.value.code is ConfigErrorCode.MISSING_EXCHANGE_KEY


def test_futures_config_requires_margin_mode(tmp_path: Path) -> None:
    # Given
    config_path = _write_config(
        tmp_path,
        (
            "exchange:",
            "  trading_mode: futures",
        ),
    )

    # When
    with pytest.raises(ConfigLoadError) as exc_info:
        load_runtime_settings(config_path)

    # Then
    assert exc_info.value.code is ConfigErrorCode.FUTURES_MARGIN_MODE_REQUIRED


def test_env_override_wins_when_nested_setting_is_present(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Given
    config_path = _write_config(
        tmp_path,
        (
            "exchange:",
            "  trading_mode: spot",
            "risk:",
            '  stake_usdt: "10"',
        ),
    )
    monkeypatch.setenv("NFI_ENGINE__RISK__STAKE_USDT", "25")

    # When
    settings = load_runtime_settings(config_path)

    # Then
    assert settings.risk.stake_usdt == 25


def test_frontend_metadata_marks_safe_sensitive_and_restart_fields() -> None:
    # Given
    metadata = frontend_metadata()

    # When
    risk_stake = _find_metadata(metadata, "risk.stake_usdt")
    exchange_key = _find_metadata(metadata, "exchange.api_key")
    api_host = _find_metadata(metadata, "api.host")

    # Then
    assert risk_stake.frontend_editable is True
    assert risk_stake.runtime_apply_safe is True
    assert exchange_key.sensitive is True
    assert api_host.restart_required is True


def _write_config(tmp_path: Path, lines: tuple[str, ...]) -> Path:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path


def _find_metadata(metadata: tuple[FieldMetadata, ...], path: str) -> FieldMetadata:
    for item in metadata:
        if item.path == path:
            return item
    raise AssertionError(path)
