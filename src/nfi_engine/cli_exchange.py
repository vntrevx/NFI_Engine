from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Annotated, Final, NoReturn

import anyio
import typer

from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.domain import (
    DomainError,
    Leverage,
    OrderType,
    PositionSide,
    Price,
    Quantity,
    TradingPair,
)
from nfi_engine.exchange import ExchangeError, ExchangeOrder, ExchangeOrderRequest, Tick
from nfi_engine.exchange.bybit import BybitTestnetAdapter
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.reconciliation import (
    ReconciliationError,
    ReconciliationReport,
    load_reconciliation_fixture,
    reconcile_snapshot,
)

exchange_app: Final[typer.Typer] = typer.Typer(help="Inspect exchange adapter behavior.")
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
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
) -> None:
    try:
        settings = load_runtime_settings(config)
        if settings.exchange.name == "bybit":
            BybitTestnetAdapter.from_settings(settings=settings, client=None)
        sys.stdout.write(f"exchange={settings.exchange.name}\n")
        sys.stdout.write("live_exchange=false\n")
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except ExchangeError as exc:
        _exit_with_error(exc.code.value, exc.message)


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
