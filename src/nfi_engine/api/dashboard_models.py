from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from nfi_engine.api.dashboard_truth_models import (
    DashboardAccountTruthResponse,
    DashboardExecutionEventResponse,
    DashboardExecutionFillResponse,
    DashboardExecutionIntentResponse,
    DashboardExecutionOrderResponse,
)
from nfi_engine.dashboard.models import (
    DashboardAction,
    DashboardClosedTradeSummary,
    DashboardEquityPoint,
    DashboardError,
    DashboardExecutionSignal,
    DashboardOpenPosition,
    DashboardPricePoint,
    DashboardReadiness,
    DashboardRecentTrade,
    DashboardSnapshot,
)


class StrictDashboardApiModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


class DashboardReadinessCheckResponse(StrictDashboardApiModel):
    code: str
    status: str
    message: str


class DashboardReadinessResponse(StrictDashboardApiModel):
    profile: str
    blocked: bool
    checks: tuple[DashboardReadinessCheckResponse, ...]

    @classmethod
    def from_readiness(cls, readiness: DashboardReadiness) -> DashboardReadinessResponse:
        return cls(
            profile=readiness.profile,
            blocked=readiness.blocked,
            checks=tuple(
                DashboardReadinessCheckResponse(
                    code=check.code,
                    status=check.status,
                    message=check.message,
                )
                for check in readiness.checks
            ),
        )


class DashboardActionResponse(StrictDashboardApiModel):
    code: str
    severity: str
    title: str
    detail: str
    target: str

    @classmethod
    def from_action(cls, action: DashboardAction) -> DashboardActionResponse:
        return cls(
            code=action.code,
            severity=action.severity,
            title=action.title,
            detail=action.detail,
            target=action.target,
        )


class DashboardExecutionSignalResponse(StrictDashboardApiModel):
    code: str
    title: str
    status: str
    detail: str

    @classmethod
    def from_signal(
        cls,
        signal: DashboardExecutionSignal,
    ) -> DashboardExecutionSignalResponse:
        return cls(
            code=signal.code,
            title=signal.title,
            status=signal.status,
            detail=signal.detail,
        )


class DashboardPairlistResponse(StrictDashboardApiModel):
    total: int
    preview: tuple[str, ...]
    quote_asset: str


class DashboardEquityPointResponse(StrictDashboardApiModel):
    at: str
    equity: str
    available: str

    @classmethod
    def from_point(cls, point: DashboardEquityPoint) -> DashboardEquityPointResponse:
        return cls(
            at=_datetime_json(point.at),
            equity=_decimal_json(point.equity),
            available=_decimal_json(point.available),
        )


class DashboardPricePointResponse(StrictDashboardApiModel):
    pair: str
    at: str
    price: str

    @classmethod
    def from_point(cls, point: DashboardPricePoint) -> DashboardPricePointResponse:
        return cls(pair=point.pair, at=_datetime_json(point.at), price=_decimal_json(point.price))


class DashboardOpenPositionResponse(StrictDashboardApiModel):
    position_id: str
    pair: str
    side: str
    quantity: str
    entry_price: str
    leverage: str
    updated_at: str

    @classmethod
    def from_position(cls, position: DashboardOpenPosition) -> DashboardOpenPositionResponse:
        return cls(
            position_id=position.position_id,
            pair=position.pair,
            side=position.side.value,
            quantity=_decimal_json(position.quantity),
            entry_price=_decimal_json(position.entry_price),
            leverage=_decimal_json(position.leverage),
            updated_at=_datetime_json(position.updated_at),
        )


class DashboardRecentTradeResponse(StrictDashboardApiModel):
    trade_id: str
    pair: str
    side: str
    state: str
    opened_at: str
    closed_at: str | None
    profit: str

    @classmethod
    def from_trade(cls, trade: DashboardRecentTrade) -> DashboardRecentTradeResponse:
        return cls(
            trade_id=trade.trade_id,
            pair=trade.pair,
            side=trade.side.value,
            state=trade.state.value,
            opened_at=_datetime_json(trade.opened_at),
            closed_at=None if trade.closed_at is None else _datetime_json(trade.closed_at),
            profit=_decimal_json(trade.profit),
        )


class DashboardClosedTradeSummaryResponse(StrictDashboardApiModel):
    closed_trades: int
    wins: int
    losses: int
    profit: str

    @classmethod
    def from_summary(
        cls,
        summary: DashboardClosedTradeSummary,
    ) -> DashboardClosedTradeSummaryResponse:
        return cls(
            closed_trades=summary.closed_trades,
            wins=summary.wins,
            losses=summary.losses,
            profit=_decimal_json(summary.profit),
        )


class DashboardErrorResponse(StrictDashboardApiModel):
    at: str
    code: str
    safe_summary: str
    correlation_id: str

    @classmethod
    def from_error(cls, error: DashboardError) -> DashboardErrorResponse:
        return cls(
            at=_datetime_json(error.at),
            code=error.code,
            safe_summary=error.safe_summary,
            correlation_id=error.correlation_id,
        )


class DashboardSnapshotResponse(StrictDashboardApiModel):
    generated_at: str
    bot_state: str
    trading_mode: str
    exchange: str
    actions: tuple[DashboardActionResponse, ...]
    readiness: DashboardReadinessResponse
    pairlist: DashboardPairlistResponse
    execution_signals: tuple[DashboardExecutionSignalResponse, ...]
    account_truth: DashboardAccountTruthResponse
    equity_points: tuple[DashboardEquityPointResponse, ...]
    price_points: tuple[DashboardPricePointResponse, ...]
    open_positions: tuple[DashboardOpenPositionResponse, ...]
    recent_trades: tuple[DashboardRecentTradeResponse, ...]
    closed_trade_summary: DashboardClosedTradeSummaryResponse
    recent_errors: tuple[DashboardErrorResponse, ...]
    execution_intents: tuple[DashboardExecutionIntentResponse, ...]
    open_execution_orders: tuple[DashboardExecutionOrderResponse, ...]
    recent_execution_fills: tuple[DashboardExecutionFillResponse, ...]
    recent_execution_events: tuple[DashboardExecutionEventResponse, ...]

    @classmethod
    def from_snapshot(cls, snapshot: DashboardSnapshot) -> DashboardSnapshotResponse:
        return cls(
            generated_at=_datetime_json(snapshot.generated_at),
            bot_state=snapshot.bot_state.value,
            trading_mode=snapshot.trading_mode,
            exchange=snapshot.exchange,
            actions=tuple(
                DashboardActionResponse.from_action(action) for action in snapshot.actions
            ),
            readiness=DashboardReadinessResponse.from_readiness(snapshot.readiness),
            pairlist=DashboardPairlistResponse(
                total=snapshot.pairlist.total,
                preview=snapshot.pairlist.preview,
                quote_asset=snapshot.pairlist.quote_asset,
            ),
            execution_signals=tuple(
                DashboardExecutionSignalResponse.from_signal(signal)
                for signal in snapshot.execution_signals
            ),
            account_truth=DashboardAccountTruthResponse.from_truth(snapshot.account_truth),
            equity_points=tuple(
                DashboardEquityPointResponse.from_point(point) for point in snapshot.equity_points
            ),
            price_points=tuple(
                DashboardPricePointResponse.from_point(point) for point in snapshot.price_points
            ),
            open_positions=tuple(
                DashboardOpenPositionResponse.from_position(position)
                for position in snapshot.open_positions
            ),
            recent_trades=tuple(
                DashboardRecentTradeResponse.from_trade(trade) for trade in snapshot.recent_trades
            ),
            closed_trade_summary=DashboardClosedTradeSummaryResponse.from_summary(
                snapshot.closed_trade_summary,
            ),
            recent_errors=tuple(
                DashboardErrorResponse.from_error(error) for error in snapshot.recent_errors
            ),
            execution_intents=tuple(
                DashboardExecutionIntentResponse.from_intent(intent)
                for intent in snapshot.execution_intents
            ),
            open_execution_orders=tuple(
                DashboardExecutionOrderResponse.from_order(order)
                for order in snapshot.open_execution_orders
            ),
            recent_execution_fills=tuple(
                DashboardExecutionFillResponse.from_fill(fill)
                for fill in snapshot.recent_execution_fills
            ),
            recent_execution_events=tuple(
                DashboardExecutionEventResponse.from_event(event)
                for event in snapshot.recent_execution_events
            ),
        )


def _datetime_json(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decimal_json(value: Decimal) -> str:
    return str(value)
