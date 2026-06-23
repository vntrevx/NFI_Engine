from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import ClassVar, Final

from pydantic import BaseModel, ConfigDict

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


class _ExchangeCapabilitiesCliPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    exchange_id: str
    source: str
    support_level: str
    trading_mode: str
    can_configure: bool
    live_trading_allowed: bool
    policy_block: str
    credential_fields: list[str]


def test_cli_help_lists_operator_commands() -> None:
    # Given
    command: Final = ["uv", "run", "nfi-engine", "--help"]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    for command_name in (
        "config",
        "benchmark",
        "strategy",
        "data",
        "exchange",
        "db",
        "backtest",
        "paper-run",
        "serve",
        "setup",
    ):
        assert command_name in result.stdout


def test_cli_config_validate_succeeds_for_spot_paper_config() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "validate",
        "--config",
        "examples/spot-paper.yaml",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "valid" in result.stdout
    assert "trading_mode=spot" in result.stdout


def test_cli_expected_config_error_returns_typed_code() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "validate",
        "--config",
        "tests/fixtures/config/live-without-confirmation.yaml",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 1
    assert "LIVE_TRADING_REQUIRES_CONFIRMATION" in result.stderr


def test_cli_backtest_json_output_parses() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "backtest",
        "--config",
        "examples/spot-paper.yaml",
        "--timerange",
        "2026-01-01:2026-01-07",
        "--json",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    pretty = subprocess.run(
        [sys.executable, "-m", "json.tool"],
        cwd=PROJECT_ROOT,
        input=result.stdout,
        capture_output=True,
        text=True,
        check=False,
    )

    # Then
    assert result.returncode == 0, result.stderr
    assert pretty.returncode == 0, pretty.stderr
    assert '"summary"' in pretty.stdout


def test_cli_paper_run_reports_no_live_orders() -> None:
    # Given
    command: Final = [
        "uv",
        "run",
        "nfi-engine",
        "paper-run",
        "--config",
        "examples/futures-paper.yaml",
        "--ticks",
        "tests/fixtures/ticks/btc_usdt_futures.jsonl",
        "--max-events",
        "3",
    ]

    # When
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)

    # Then
    assert result.returncode == 0, result.stderr
    assert "processed_events=3" in result.stdout
    assert "live_orders=false" in result.stdout


def _run_exchange_capabilities_json(*, exchange: str, trading_mode: str) -> str:
    command = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "capabilities",
        "--exchange",
        exchange,
        "--trading-mode",
        trading_mode,
        "--format",
        "json",
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    validation = subprocess.run(
        [sys.executable, "-m", "json.tool"],
        cwd=PROJECT_ROOT,
        input=result.stdout,
        capture_output=True,
        text=True,
        check=False,
    )
    assert validation.returncode == 0, validation.stderr
    return result.stdout.strip()


def _exchange_capabilities_payload(
    *,
    exchange: str,
    trading_mode: str,
) -> _ExchangeCapabilitiesCliPayload:
    return _ExchangeCapabilitiesCliPayload.model_validate_json(
        _run_exchange_capabilities_json(exchange=exchange, trading_mode=trading_mode),
    )


def test_cli_exchange_capabilities_bybit_returns_verified_testnet_json() -> None:
    payload = _exchange_capabilities_payload(exchange="bybit", trading_mode="futures")

    assert payload.exchange_id == "bybit"
    assert payload.trading_mode == "futures"
    assert payload.support_level == "verified"
    assert payload.can_configure is True
    assert payload.live_trading_allowed is False
    assert payload.policy_block == "live trading is blocked in current milestone"


def test_cli_exchange_capabilities_okx_remains_candidate_json() -> None:
    payload = _exchange_capabilities_payload(exchange="okx", trading_mode="futures")

    assert payload.exchange_id == "okx"
    assert payload.trading_mode == "futures"
    assert payload.support_level == "candidate"
    assert payload.can_configure is True
    assert payload.live_trading_allowed is False


def test_cli_exchange_capabilities_mexc_is_report_only_generic_unverified() -> None:
    payload = _exchange_capabilities_payload(exchange="mexc", trading_mode="futures")
    assert payload.exchange_id == "mexc"
    assert payload.source == "generic-discovery"
    assert payload.support_level == "generic-unverified"
    assert payload.can_configure is False
    assert payload.live_trading_allowed is False
    assert "evidence" in payload.policy_block.lower()
    assert payload.credential_fields == []


def test_cli_exchange_capabilities_mexc_json_does_not_promote_to_config_execution(
    tmp_path: Path,
) -> None:
    temporary_config = """
exchange:
  name: mexc
  trading_mode: futures
  margin_mode: isolated
  testnet: true
"""
    config_path = tmp_path / "mexc-futures.yaml"
    config_path.write_text(temporary_config.strip() + "\n", encoding="utf-8")
    command = [
        "uv",
        "run",
        "nfi-engine",
        "config",
        "validate",
        "--config",
        str(config_path),
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert "EXCHANGE_UNSUPPORTED" in result.stderr


def test_cli_exchange_check_rejects_unsafe_exchange_id_before_stdout() -> None:
    command = [
        "uv",
        "run",
        "nfi-engine",
        "exchange",
        "check",
        "--exchange",
        "bad\nline",
    ]
    result = subprocess.run(command, cwd=PROJECT_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 1
    assert result.stdout == ""
    assert "EXCHANGE_ID_INVALID" in result.stderr
