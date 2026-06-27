from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated, Final, NoReturn

import anyio
import typer

from nfi_engine.cli_exchange_capabilities import (
    ExchangeCapabilitiesFormat,
    build_exchange_capabilities_output,
    format_capability_profile,
)
from nfi_engine.cli_exchange_lifecycle import lifecycle_app
from nfi_engine.cli_exchange_runtime import runtime_check
from nfi_engine.cli_exchange_testnet import (
    run_testnet_execute_cli,
    write_testnet_pilot_report,
)
from nfi_engine.config import ConfigLoadError, RuntimeSettings, load_runtime_settings
from nfi_engine.domain import (
    DomainError,
    Leverage,
    OrderType,
    PositionSide,
    Price,
    Quantity,
    TradingMode,
    TradingPair,
)
from nfi_engine.exchange import (
    ExchangeCapabilityProfile,
    ExchangeError,
    ExchangeOrder,
    ExchangeOrderRequest,
    Tick,
    get_exchange_profile,
)
from nfi_engine.exchange.discovery import parse_exchange_id
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.exchange.testnet_pilot import build_testnet_pilot_report
from nfi_engine.reconciliation import (
    ReconciliationError,
    ReconciliationReport,
    load_reconciliation_fixture,
    reconcile_snapshot,
)

exchange_app: Final[typer.Typer] = typer.Typer(
    help="Inspect exchange registry and simulator behavior."
)
exchange_app.add_typer(lifecycle_app, name="lifecycle")
exchange_app.command(name="runtime-check")(runtime_check)
exchange_app.command(name="testnet-execute")(run_testnet_execute_cli)
DEFAULT_PRICE: Final = Decimal(100)
DEFAULT_RECONCILE_FIXTURE: Final = Path("tests/fixtures/exchange/reconcile_match.json")


@exchange_app.command("simulate-order")
def simulate_order(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    pair: Annotated[str, typer.Option("--pair")],
    side: Annotated[str, typer.Option("--side")],
    order_type: Annotated[str, typer.Option("--type")],
    stake: Annotated[str, typer.Option("--stake")],
) -> None:
    try:
        settings = load_runtime_settings(config)
        parsed_pair = TradingPair.parse(pair, settings.exchange.trading_mode)
        quantity = Quantity(_parse_decimal(stake, "stake") / DEFAULT_PRICE)
        request = ExchangeOrderRequest(
            pair=parsed_pair,
            side=_parse_side(side),
            order_type=_parse_order_type(order_type),
            quantity=quantity,
            price=None,
            leverage=Leverage.parse(settings.risk.leverage),
        )
        order = anyio.run(_simulate_order, request)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except DomainError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except ExchangeError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except InvalidOperation as exc:
        _exit_with_error("EXCHANGE_DECIMAL_INVALID", str(exc))
    sys.stdout.write(f"order_state={order.state.value}\n")
    sys.stdout.write(f"live_exchange={str(order.live_exchange).lower()}\n")
    sys.stdout.write(f"filled_price={order.filled_price}\n")


@exchange_app.command("check")
def check_exchange(
    config: Annotated[Path | None, typer.Option("--config", exists=True, dir_okay=False)] = None,
    exchange: Annotated[str | None, typer.Option("--exchange")] = None,
) -> None:
    try:
        exchange_id, settings = _exchange_check_target(config=config, exchange=exchange)
        sys.stdout.write(f"exchange={exchange_id}\n")
        profile = get_exchange_profile(exchange_id)
        if profile is None:
            _exit_with_error(
                "EXCHANGE_UNSUPPORTED",
                f"unsupported exchange: {exchange_id}",
            )
        sys.stdout.write(format_capability_profile(profile))
        if settings is not None:
            _write_config_policy(settings=settings, profile=profile)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except ExchangeError as exc:
        _exit_with_error(exc.code.value, exc.message)


@exchange_app.command("capabilities")
def exchange_capabilities(
    exchange: Annotated[str, typer.Option("--exchange")],
    trading_mode: Annotated[
        TradingMode,
        typer.Option("--trading-mode"),
    ] = TradingMode.SPOT,
    output_format: Annotated[
        ExchangeCapabilitiesFormat,
        typer.Option("--format"),
    ] = ExchangeCapabilitiesFormat.TEXT,
) -> None:
    try:
        output = build_exchange_capabilities_output(
            exchange=exchange,
            trading_mode=trading_mode,
            output_format=output_format,
        )
    except ExchangeError as exc:
        _exit_with_error(exc.code.value, exc.message)
    sys.stdout.write(output)


@exchange_app.command("testnet-pilot")
def exchange_testnet_pilot(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    json_output: Annotated[bool, typer.Option("--json/--text")] = False,
) -> None:
    try:
        settings = load_runtime_settings(config)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    report = build_testnet_pilot_report(settings=settings)
    if json_output:
        sys.stdout.write(report.model_dump_json(indent=2) + "\n")
        return
    write_testnet_pilot_report(report)


@exchange_app.command("reconcile")
def reconcile_exchange(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    dry_run: Annotated[bool, typer.Option("--dry-run/--apply")] = True,
    fixture: Annotated[
        Path,
        typer.Option("--fixture", exists=True, dir_okay=False),
    ] = DEFAULT_RECONCILE_FIXTURE,
) -> None:
    try:
        load_runtime_settings(config)
        snapshot = load_reconciliation_fixture(fixture)
        report = reconcile_snapshot(snapshot=snapshot, dry_run=dry_run)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except ReconciliationError as exc:
        _exit_with_error(exc.code.value, exc.message)
    _write_reconciliation_report(report)
    if report.trading_halted:
        raise typer.Exit(code=1)


async def _simulate_order(request: ExchangeOrderRequest) -> ExchangeOrder:
    tick = Tick(pair=request.pair, price=Price(DEFAULT_PRICE), at=datetime(2026, 1, 1, tzinfo=UTC))
    simulator = DeterministicExchangeSimulator(ticks=(tick,))
    return await simulator.create_order(request)


def _write_reconciliation_report(report: ReconciliationReport) -> None:
    sys.stdout.write("reconciliation=exchange\n")
    sys.stdout.write(f"apply={str(report.apply).lower()}\n")
    sys.stdout.write(f"trading_halted={str(report.trading_halted).lower()}\n")
    sys.stdout.write(f"mismatch_count={report.mismatch_count}\n")
    for issue in report.issues:
        sys.stdout.write(
            f"issue={issue.code.value}\tsubject={issue.subject}\taction={issue.suggested_action}\n",
        )


def _exchange_check_target(
    *,
    config: Path | None,
    exchange: str | None,
) -> tuple[str, RuntimeSettings | None]:
    if config is None and exchange is None:
        _exit_with_error("EXCHANGE_CHECK_TARGET_REQUIRED", "pass --config or --exchange")
    if config is not None and exchange is not None:
        _exit_with_error(
            "EXCHANGE_CHECK_TARGET_AMBIGUOUS", "pass only one of --config or --exchange"
        )
    if exchange is not None:
        return parse_exchange_id(exchange), None
    if config is None:
        _exit_with_error("EXCHANGE_CHECK_TARGET_REQUIRED", "pass --config or --exchange")
    settings = load_runtime_settings(config)
    return settings.exchange.name, settings


def _write_config_policy(
    *,
    settings: RuntimeSettings,
    profile: ExchangeCapabilityProfile,
) -> None:
    block_reason = _exchange_config_block_reason(settings=settings, profile=profile)
    sys.stdout.write(f"config_live_trading={str(settings.engine.live_trading).lower()}\n")
    sys.stdout.write(f"config_testnet={str(settings.exchange.testnet).lower()}\n")
    if block_reason is None:
        sys.stdout.write("policy_status=pass\n")
        return
    sys.stdout.write("policy_status=block\n")
    sys.stdout.write(f"policy_block={block_reason}\n")
    raise typer.Exit(code=1)


def _exchange_config_block_reason(
    *,
    settings: RuntimeSettings,
    profile: ExchangeCapabilityProfile,
) -> str | None:
    if settings.engine.live_trading:
        return "live_trading is blocked in current milestone"
    if profile.exchange_id != "simulator" and not settings.exchange.testnet:
        return f"{profile.exchange_id} requires testnet=true in current milestone"
    if settings.exchange.testnet and not profile.supports_testnet:
        return f"{profile.exchange_id} has no registry-backed testnet support"
    return None


def _parse_side(raw: str) -> PositionSide:
    try:
        return PositionSide(raw.lower())
    except ValueError as exc:
        code = "EXCHANGE_SIDE_INVALID"
        message = f"invalid side: {raw}"
        raise _exit_with_error(code, message) from exc


def _parse_order_type(raw: str) -> OrderType:
    try:
        return OrderType(raw.lower())
    except ValueError as exc:
        code = "EXCHANGE_ORDER_TYPE_INVALID"
        message = f"invalid order type: {raw}"
        raise _exit_with_error(code, message) from exc


def _parse_decimal(raw: str, field_name: str) -> Decimal:
    value = Decimal(raw)
    if not value.is_finite():
        _exit_with_error("EXCHANGE_DECIMAL_INVALID", f"{field_name} must be finite")
    return value


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
