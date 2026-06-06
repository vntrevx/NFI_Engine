from __future__ import annotations

import hashlib
from decimal import Decimal
from enum import StrEnum, unique
from pathlib import Path
from typing import ClassVar, Final, NotRequired, TypedDict, assert_never

from pydantic import BaseModel, ConfigDict, Field

from nfi_engine.domain import OrderState, OrderType, PositionSide

EIGHT_PLACES: Final = Decimal("0.00000001")
QUOTE_WRAPPER_LENGTH: Final = 2
SIMULATOR_WARNING: Final = "approximation_not_live_exchange_fidelity"


@unique
class FeeModel(StrEnum):
    MAKER = "maker"
    TAKER = "taker"


class FillScenario(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    name: str
    seed: int
    pair: str
    side: PositionSide
    order_type: OrderType
    quantity: Decimal = Field(gt=Decimal(0))
    reference_price: Decimal = Field(gt=Decimal(0))
    partial_fill_ratio: Decimal = Field(ge=Decimal(0), le=Decimal(1))
    latency_ms: int = Field(ge=0)
    fee_model: FeeModel
    maker_fee_rate: Decimal = Field(ge=Decimal(0))
    taker_fee_rate: Decimal = Field(ge=Decimal(0))
    funding_rate: Decimal
    slippage_pct: Decimal
    slippage_anomaly_threshold_pct: Decimal = Field(ge=Decimal(0))
    exchange_reject: bool
    liquidation_near_miss: bool
    scenario_hash: str


class FillSimulationResult(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    scenario_hash: str
    seed: int
    pair: str
    order_state: str
    filled_quantity: str
    remaining_quantity: str
    execution_price: str
    latency_ms: int
    fee_model: str
    fee_paid: str
    funding_fee: str
    slippage_pct: str
    circuit_breaker_event: bool
    liquidation_near_miss: bool
    events: tuple[str, ...]
    simulator_warning: str


class FillSimulationPayload(TypedDict):
    scenario_hash: str
    seed: int
    pair: str
    order_state: str
    filled_quantity: str
    remaining_quantity: str
    execution_price: str
    latency_ms: int
    fee_model: str
    fee_paid: str
    funding_fee: str
    slippage_pct: str
    circuit_breaker_event: bool
    liquidation_near_miss: bool
    events: list[str]
    simulator_warning: NotRequired[str]


def load_fill_scenario(path: Path) -> FillScenario:
    content = path.read_text(encoding="utf-8")
    raw = _parse_flat_yaml(content)
    payload = raw | {"scenario_hash": hashlib.sha256(content.encode("utf-8")).hexdigest()}
    return FillScenario.model_validate(payload)


def simulate_fill_scenario(scenario: FillScenario) -> FillSimulationResult:
    if scenario.exchange_reject:
        return _rejected_result(scenario)
    filled_quantity = _quantize(scenario.quantity * scenario.partial_fill_ratio)
    remaining_quantity = _quantize(scenario.quantity - filled_quantity)
    execution_price = _execution_price(scenario)
    notional = filled_quantity * execution_price
    fee_paid = _quantize(notional * _fee_rate(scenario))
    funding_fee = _quantize(filled_quantity * scenario.reference_price * scenario.funding_rate)
    events = _events(
        scenario=scenario,
        state=_order_state(scenario),
        circuit_breaker_event=_circuit_breaker_event(scenario),
    )
    return FillSimulationResult(
        scenario_hash=scenario.scenario_hash,
        seed=scenario.seed,
        pair=scenario.pair,
        order_state=_order_state(scenario).name,
        filled_quantity=_format_decimal(filled_quantity),
        remaining_quantity=_format_decimal(remaining_quantity),
        execution_price=_format_decimal(execution_price),
        latency_ms=scenario.latency_ms,
        fee_model=scenario.fee_model.value,
        fee_paid=_format_decimal(fee_paid),
        funding_fee=_format_decimal(funding_fee),
        slippage_pct=_format_decimal(scenario.slippage_pct),
        circuit_breaker_event=_circuit_breaker_event(scenario),
        liquidation_near_miss=scenario.liquidation_near_miss,
        events=events,
        simulator_warning=SIMULATOR_WARNING,
    )


def fill_result_payload(result: FillSimulationResult) -> FillSimulationPayload:
    payload = FillSimulationPayload(
        scenario_hash=result.scenario_hash,
        seed=result.seed,
        pair=result.pair,
        order_state=result.order_state,
        filled_quantity=result.filled_quantity,
        remaining_quantity=result.remaining_quantity,
        execution_price=result.execution_price,
        latency_ms=result.latency_ms,
        fee_model=result.fee_model,
        fee_paid=result.fee_paid,
        funding_fee=result.funding_fee,
        slippage_pct=result.slippage_pct,
        circuit_breaker_event=result.circuit_breaker_event,
        liquidation_near_miss=result.liquidation_near_miss,
        events=list(result.events),
    )
    payload["simulator_warning"] = result.simulator_warning
    return payload


def _rejected_result(scenario: FillScenario) -> FillSimulationResult:
    return FillSimulationResult(
        scenario_hash=scenario.scenario_hash,
        seed=scenario.seed,
        pair=scenario.pair,
        order_state=OrderState.REJECTED.name,
        filled_quantity=_format_decimal(Decimal(0)),
        remaining_quantity=_format_decimal(scenario.quantity),
        execution_price=_format_decimal(scenario.reference_price),
        latency_ms=scenario.latency_ms,
        fee_model=scenario.fee_model.value,
        fee_paid=_format_decimal(Decimal(0)),
        funding_fee=_format_decimal(Decimal(0)),
        slippage_pct=_format_decimal(scenario.slippage_pct),
        circuit_breaker_event=True,
        liquidation_near_miss=scenario.liquidation_near_miss,
        events=("EXCHANGE_REJECT",),
        simulator_warning=SIMULATOR_WARNING,
    )


def _order_state(scenario: FillScenario) -> OrderState:
    if scenario.partial_fill_ratio < Decimal(1):
        return OrderState.PARTIALLY_FILLED
    return OrderState.FILLED


def _execution_price(scenario: FillScenario) -> Decimal:
    match scenario.side:
        case PositionSide.LONG:
            multiplier = Decimal(1) + scenario.slippage_pct
        case PositionSide.SHORT:
            multiplier = Decimal(1) - scenario.slippage_pct
        case unreachable:
            assert_never(unreachable)
    return _quantize(scenario.reference_price * multiplier)


def _fee_rate(scenario: FillScenario) -> Decimal:
    match scenario.fee_model:
        case FeeModel.MAKER:
            return scenario.maker_fee_rate
        case FeeModel.TAKER:
            return scenario.taker_fee_rate
        case unreachable:
            assert_never(unreachable)


def _circuit_breaker_event(scenario: FillScenario) -> bool:
    return (
        abs(scenario.slippage_pct) > scenario.slippage_anomaly_threshold_pct
        or scenario.liquidation_near_miss
    )


def _events(
    *,
    scenario: FillScenario,
    state: OrderState,
    circuit_breaker_event: bool,
) -> tuple[str, ...]:
    events: tuple[str, ...] = ()
    if state is OrderState.PARTIALLY_FILLED:
        events += ("PARTIAL_FILL",)
    if scenario.latency_ms > 0:
        events += ("LATENCY_APPLIED",)
    if scenario.funding_rate != Decimal(0):
        events += ("FUNDING_FEE_ACCRUED",)
    if abs(scenario.slippage_pct) > scenario.slippage_anomaly_threshold_pct:
        events += ("SLIPPAGE_ANOMALY",)
    if scenario.liquidation_near_miss:
        events += ("LIQUIDATION_NEAR_MISS",)
    if circuit_breaker_event:
        events += ("CIRCUIT_BREAKER_EVENT",)
    return events


def _parse_flat_yaml(content: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if line == "" or line.startswith("#"):
            continue
        key, separator, value = line.partition(":")
        if separator != ":":
            continue
        values[key.strip()] = _unquote(value.strip())
    return values


def _unquote(value: str) -> str:
    if len(value) >= QUOTE_WRAPPER_LENGTH and value[0] == '"' and value[-1] == '"':
        return value[1:-1]
    return value


def _quantize(value: Decimal) -> Decimal:
    return value.quantize(EIGHT_PLACES)


def _format_decimal(value: Decimal) -> str:
    return f"{_quantize(value):f}"
