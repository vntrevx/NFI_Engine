from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum, unique
from typing import ClassVar, override

from pydantic import BaseModel, ConfigDict

from nfi_engine.domain import MarginMode, OrderState, PositionSide


@unique
class ReconciliationCode(StrEnum):
    ORPHAN_LOCAL_ORDER = "ORPHAN_LOCAL_ORDER"
    ORPHAN_EXCHANGE_ORDER = "ORPHAN_EXCHANGE_ORDER"
    POSITION_MISMATCH = "POSITION_MISMATCH"
    BALANCE_MISMATCH = "BALANCE_MISMATCH"
    LEVERAGE_MISMATCH = "LEVERAGE_MISMATCH"
    MARGIN_MODE_MISMATCH = "MARGIN_MODE_MISMATCH"
    STALE_LOCK = "STALE_LOCK"
    DUPLICATE_LOCAL_TRADE = "DUPLICATE_LOCAL_TRADE"
    MISSING_EXCHANGE_FILL = "MISSING_EXCHANGE_FILL"
    PENDING_CANCEL = "PENDING_CANCEL"


@unique
class ReconciliationErrorCode(StrEnum):
    FIXTURE_INVALID = "FIXTURE_INVALID"
    FIXTURE_NOT_READABLE = "FIXTURE_NOT_READABLE"


@dataclass(frozen=True, slots=True)
class ReconciliationError(Exception):
    code: ReconciliationErrorCode
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"


class StrictReconciliationModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


class OrderSnapshot(StrictReconciliationModel):
    order_id: str
    pair: str
    state: OrderState
    pending_cancel: bool = False


class PositionSnapshot(StrictReconciliationModel):
    pair: str
    side: PositionSide
    quantity: Decimal
    leverage: Decimal
    margin_mode: MarginMode | None


class BalanceSnapshot(StrictReconciliationModel):
    asset: str
    total: Decimal
    available: Decimal


class TradeSnapshot(StrictReconciliationModel):
    trade_id: str


class LockSnapshot(StrictReconciliationModel):
    name: str
    stale: bool


class ReconciliationSideSnapshot(StrictReconciliationModel):
    open_orders: tuple[OrderSnapshot, ...] = ()
    closed_orders: tuple[OrderSnapshot, ...] = ()
    positions: tuple[PositionSnapshot, ...] = ()
    balances: tuple[BalanceSnapshot, ...] = ()
    trades: tuple[TradeSnapshot, ...] = ()
    locks: tuple[LockSnapshot, ...] = ()


class ReconciliationSnapshot(StrictReconciliationModel):
    local: ReconciliationSideSnapshot
    exchange: ReconciliationSideSnapshot


class ReconciliationIssue(StrictReconciliationModel):
    code: ReconciliationCode
    subject: str
    message: str
    blocks_trading: bool
    suggested_action: str


class ReconciliationReport(StrictReconciliationModel):
    apply: bool
    trading_halted: bool
    mismatch_count: int
    issues: tuple[ReconciliationIssue, ...]
