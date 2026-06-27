from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


class _RuntimeCheckPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    exchange_id: str
    trading_mode: str
    runtime_verified: bool
    promotion_ready: bool
    blockers: tuple[str, ...]


class _RuntimeCheckCollectionPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    reports: tuple[_RuntimeCheckPayload, ...]


def test_exchange_runtime_check_reports_bitvavo_missing_operator_id(
    tmp_path: Path,
) -> None:
    # Given
    config_path = tmp_path / "bitvavo.yaml"
    config_path.write_text(
        """exchange:
  name: bitvavo
  trading_mode: spot
  testnet: true
  api_key: key
  api_secret: secret
""",
        encoding="utf-8",
    )
    command = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "runtime-check",
        "--config",
        str(config_path),
        "--format",
        "json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    validation = subprocess.run(
        [sys.executable, "-m", "json.tool"],
        cwd=PROJECT_ROOT,
        input=result.stdout,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = _RuntimeCheckPayload.model_validate_json(result.stdout)

    # Then
    assert result.returncode == 0, result.stderr
    assert validation.returncode == 0, validation.stderr
    assert payload.exchange_id == "bitvavo"
    assert payload.runtime_verified is True
    assert payload.promotion_ready is False
    assert "RUNTIME_CREDENTIALS_MISSING" in payload.blockers


def test_exchange_runtime_check_promotes_binance_futures_with_testnet_config(
    tmp_path: Path,
) -> None:
    # Given
    config_path = tmp_path / "binance-futures.yaml"
    config_path.write_text(
        """exchange:
  name: binance
  trading_mode: futures
  margin_mode: isolated
  testnet: true
  api_key: key
  api_secret: secret
""",
        encoding="utf-8",
    )
    command = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "runtime-check",
        "--config",
        str(config_path),
        "--format",
        "json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    validation = subprocess.run(
        [sys.executable, "-m", "json.tool"],
        cwd=PROJECT_ROOT,
        input=result.stdout,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = _RuntimeCheckPayload.model_validate_json(result.stdout)

    # Then
    assert result.returncode == 0, result.stderr
    assert validation.returncode == 0, validation.stderr
    assert payload.exchange_id == "binance"
    assert payload.trading_mode == "futures"
    assert payload.runtime_verified is True
    assert payload.promotion_ready is True
    assert payload.blockers == ()


def test_exchange_runtime_check_all_reports_json_collection() -> None:
    # Given
    command = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "runtime-check",
        "--all",
        "--format",
        "json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    validation = subprocess.run(
        [sys.executable, "-m", "json.tool"],
        cwd=PROJECT_ROOT,
        input=result.stdout,
        capture_output=True,
        text=True,
        check=False,
    )
    payload = _RuntimeCheckCollectionPayload.model_validate_json(result.stdout)

    # Then
    assert result.returncode == 0, result.stderr
    assert validation.returncode == 0, validation.stderr
    assert len(payload.reports) == 21
    assert all(report.runtime_verified for report in payload.reports)
    assert any(report.exchange_id == "bybit" for report in payload.reports)
    assert any(report.exchange_id == "binance" for report in payload.reports)
