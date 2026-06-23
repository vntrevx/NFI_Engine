from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Annotated, ClassVar, Final, NoReturn

import anyio
import typer
from pydantic import BaseModel, ConfigDict

from nfi_engine.config import ConfigLoadError, RuntimeSettings, load_runtime_settings
from nfi_engine.domain import (
    ExecutionReport,
    Leverage,
    LiquidationBuffer,
    OrderId,
    OrderState,
    OrderType,
    Position,
    PositionSide,
    Price,
    Quantity,
    TradeId,
    TradeState,
    TradingMode,
    TradingPair,
)
from nfi_engine.exchange import ExchangeError, ExchangeOrderRequest, Tick
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.orders import apply_execution_report
from nfi_engine.preflight import PreflightReport, PreflightStatus
from nfi_engine.preflight.service import run_preflight

lifecycle_app: Final[typer.Typer] = typer.Typer(
    help="Run safe exchange order lifecycle smoke checks."
)
NOW: Final = datetime(2026, 1, 1, tzinfo=UTC)
DEFAULT_LIFECYCLE_PAIR: Final = "BTC/USDT:USDT"
DEFAULT_PROFILE: Final = "bybit-testnet"


class LifecycleOperationPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    state: str


class LifecycleSmokePayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    exchange: str
    trading_mode: str
    testnet: bool
    live_exchange: bool
    preflight_blocked: bool
    deterministic_order_id: str
    operations: tuple[LifecycleOperationPayload, ...]
    funding_supported: bool
    leverage: str


@lifecycle_app.command("smoke")
def lifecycle_smoke(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    json_output: Annotated[bool, typer.Option("--json/--text")] = False,
) -> None:
    try:
        settings = load_runtime_settings(config)
        payload = anyio.run(_build_lifecycle_smoke, settings, config)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except ExchangeError as exc:
        _exit_with_error(exc.code.value, exc.message)
    if json_output:
        sys.stdout.write(payload.model_dump_json(indent=2) + "\n")
        return
    _write_text(payload)


async def _build_lifecycle_smoke(
    settings: RuntimeSettings,
    config: Path,
) -> LifecycleSmokePayload:
    preflight = run_preflight(settings=settings, profile_name=DEFAULT_PROFILE, config_path=config)
    if preflight.blocked:
        _exit_with_preflight_block(preflight)
    pair = _lifecycle_pair(settings)
    simulator = DeterministicExchangeSimulator(
        ticks=(Tick(pair=pair, price=Price(Decimal(100)), at=NOW, funding_rate=Decimal("0.0001")),),
    )
    request = ExchangeOrderRequest(
        pair=pair,
        side=PositionSide.LONG,
        order_type=OrderType.LIMIT,
        quantity=Quantity(Decimal("0.25")),
        price=Price(Decimal(99)),
        leverage=Leverage.parse("3"),
    )
    created = await simulator.create_order(request)
    fetched = await simulator.fetch_order(created.order_id, pair)
    canceled = await simulator.cancel_order(created.order_id, pair)
    leverage = await simulator.set_leverage(pair=pair, leverage=Leverage.parse("3"))
    funding = await simulator.fetch_funding_rate(pair)
    partial = _position_update_state(OrderState.PARTIALLY_FILLED)
    rejected = _position_update_state(OrderState.REJECTED)
    return LifecycleSmokePayload(
        exchange=settings.exchange.name,
        trading_mode=settings.exchange.trading_mode.value,
        testnet=settings.exchange.testnet,
        live_exchange=created.live_exchange or fetched.live_exchange or canceled.live_exchange,
        preflight_blocked=preflight.blocked,
        deterministic_order_id=created.order_id,
        operations=(
            LifecycleOperationPayload(name="create_order", state=created.state.value),
            LifecycleOperationPayload(name="fetch_order", state=fetched.state.value),
            LifecycleOperationPayload(name="cancel_order", state=canceled.state.value),
            LifecycleOperationPayload(name="partial_fill_report", state=partial.value),
            LifecycleOperationPayload(name="rejected_report", state=rejected.value),
        ),
        funding_supported=funding.supported,
        leverage=str(leverage.value),
    )


def _lifecycle_pair(settings: RuntimeSettings) -> TradingPair:
    return TradingPair.parse(DEFAULT_LIFECYCLE_PAIR, settings.exchange.trading_mode)


def _position_update_state(state: OrderState) -> OrderState:
    update = apply_execution_report(
        position=Position(
            trade_id=TradeId("lifecycle-position"),
            pair=TradingPair.parse(DEFAULT_LIFECYCLE_PAIR, TradingMode.FUTURES),
            side=PositionSide.LONG,
            quantity=Quantity(Decimal("0.25")),
            entry_price=Price(Decimal(100)),
            leverage=Leverage.parse("3"),
            liquidation_buffer=LiquidationBuffer.parse("0.05"),
            state=TradeState.OPEN,
        ),
        report=ExecutionReport(
            order_id=OrderId(f"lifecycle-{state.value}"),
            state=state,
            filled_quantity=Quantity(Decimal("0.10")),
            average_price=Price(Decimal(100)),
            reason=None,
        ),
    )
    return update.order_state


def _exit_with_preflight_block(report: PreflightReport) -> NoReturn:
    blockers = tuple(
        check.code.value for check in report.checks if check.status is PreflightStatus.BLOCK
    )
    message = ",".join(blockers) if blockers else "preflight blocked"
    _exit_with_error("EXCHANGE_LIFECYCLE_PREFLIGHT_BLOCKED", message)


def _write_text(payload: LifecycleSmokePayload) -> None:
    sys.stdout.write(f"exchange={payload.exchange}\n")
    sys.stdout.write(f"trading_mode={payload.trading_mode}\n")
    sys.stdout.write(f"testnet={str(payload.testnet).lower()}\n")
    sys.stdout.write(f"live_exchange={str(payload.live_exchange).lower()}\n")
    sys.stdout.write(f"order_id={payload.deterministic_order_id}\n")
    for operation in payload.operations:
        sys.stdout.write(f"operation={operation.name}\tstate={operation.state}\n")


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)
