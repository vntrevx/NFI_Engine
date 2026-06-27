from __future__ import annotations

import json
import sys
from enum import StrEnum, unique
from pathlib import Path
from typing import Annotated, NoReturn, assert_never

import typer

from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.domain import TradingMode
from nfi_engine.exchange import ExchangeError
from nfi_engine.exchange.runtime_verification import (
    ExchangeRuntimeReport,
    ExchangeRuntimeReportPayload,
    build_exchange_runtime_collection_payload,
    build_exchange_runtime_report,
    build_exchange_runtime_report_for_profile,
)


@unique
class ExchangeRuntimeFormat(StrEnum):
    TEXT = "text"
    JSON = "json"


def runtime_check(
    config: Annotated[Path | None, typer.Option("--config", exists=True, dir_okay=False)] = None,
    exchange: Annotated[str | None, typer.Option("--exchange")] = None,
    trading_mode: Annotated[TradingMode, typer.Option("--trading-mode")] = TradingMode.SPOT,
    all_profiles: Annotated[bool, typer.Option("--all")] = False,
    output_format: Annotated[
        ExchangeRuntimeFormat,
        typer.Option("--format"),
    ] = ExchangeRuntimeFormat.TEXT,
) -> None:
    try:
        output = _build_output(
            config=config,
            exchange=exchange,
            trading_mode=trading_mode,
            all_profiles=all_profiles,
            output_format=output_format,
        )
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except ExchangeError as exc:
        _exit_with_error(exc.code.value, exc.message)
    sys.stdout.write(output)


def _build_output(
    *,
    config: Path | None,
    exchange: str | None,
    trading_mode: TradingMode,
    all_profiles: bool,
    output_format: ExchangeRuntimeFormat,
) -> str:
    if all_profiles:
        _reject_all_target_mix(config=config, exchange=exchange)
        return _format_collection(output_format)
    report = _target_report(config=config, exchange=exchange, trading_mode=trading_mode)
    return _format_report(report=report, output_format=output_format)


def _target_report(
    *,
    config: Path | None,
    exchange: str | None,
    trading_mode: TradingMode,
) -> ExchangeRuntimeReport:
    if config is not None and exchange is not None:
        _exit_with_error(
            "EXCHANGE_RUNTIME_TARGET_AMBIGUOUS",
            "pass only one of --config or --exchange",
        )
    if config is not None:
        return build_exchange_runtime_report(settings=load_runtime_settings(config))
    if exchange is None:
        _exit_with_error("EXCHANGE_RUNTIME_TARGET_REQUIRED", "pass --config, --exchange, or --all")
    return build_exchange_runtime_report_for_profile(
        exchange_id=exchange,
        trading_mode=trading_mode,
    )


def _reject_all_target_mix(*, config: Path | None, exchange: str | None) -> None:
    if config is not None or exchange is not None:
        _exit_with_error(
            "EXCHANGE_RUNTIME_TARGET_AMBIGUOUS",
            "pass --all without --config or --exchange",
        )


def _format_collection(output_format: ExchangeRuntimeFormat) -> str:
    payload = build_exchange_runtime_collection_payload()
    match output_format:
        case ExchangeRuntimeFormat.JSON:
            return json.dumps(payload, indent=2, sort_keys=True) + "\n"
        case ExchangeRuntimeFormat.TEXT:
            return "\n".join(_format_payload_text(report) for report in payload["reports"])
        case unreachable:
            assert_never(unreachable)


def _format_report(
    *,
    report: ExchangeRuntimeReport,
    output_format: ExchangeRuntimeFormat,
) -> str:
    match output_format:
        case ExchangeRuntimeFormat.JSON:
            return json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n"
        case ExchangeRuntimeFormat.TEXT:
            return _format_payload_text(report.to_payload())
        case unreachable:
            assert_never(unreachable)


def _format_payload_text(payload: ExchangeRuntimeReportPayload) -> str:
    lines = [
        f"exchange={payload['exchange_id']}",
        f"trading_mode={payload['trading_mode']}",
        f"support_level={payload['support_level']}",
        f"runtime_verified={str(payload['runtime_verified']).lower()}",
        f"promotion_ready={str(payload['promotion_ready']).lower()}",
        f"blockers={','.join(payload['blockers'])}",
    ]
    lines.extend(
        (
            f"check={check['stage']}\tstatus={check['status']}\tcode={check['code']}"
            f"\tnext_action={check['next_action']}"
        )
        for check in payload["checks"]
    )
    return "\n".join(lines) + "\n"


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
