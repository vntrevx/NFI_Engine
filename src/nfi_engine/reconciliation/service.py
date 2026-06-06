from __future__ import annotations

from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from nfi_engine.reconciliation.models import (
    BalanceSnapshot,
    LockSnapshot,
    OrderSnapshot,
    PositionSnapshot,
    ReconciliationCode,
    ReconciliationError,
    ReconciliationErrorCode,
    ReconciliationIssue,
    ReconciliationReport,
    ReconciliationSnapshot,
    TradeSnapshot,
)

type PositionKey = tuple[str, str]
type OrderIndex = dict[str, OrderSnapshot]
type PositionIndex = dict[PositionKey, PositionSnapshot]
type BalanceIndex = dict[str, BalanceSnapshot]


def load_reconciliation_fixture(path: Path) -> ReconciliationSnapshot:
    try:
        return ReconciliationSnapshot.model_validate_json(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ReconciliationError(
            code=ReconciliationErrorCode.FIXTURE_NOT_READABLE,
            message=str(exc),
        ) from exc
    except ValidationError as exc:
        raise ReconciliationError(
            code=ReconciliationErrorCode.FIXTURE_INVALID,
            message=str(exc),
        ) from exc


def reconcile_snapshot(
    *,
    snapshot: ReconciliationSnapshot,
    dry_run: bool,
) -> ReconciliationReport:
    issues = (
        _order_issues(snapshot=snapshot)
        + _position_issues(snapshot=snapshot)
        + _balance_issues(snapshot=snapshot)
        + _trade_issues(snapshot.local.trades)
        + _lock_issues(snapshot.local.locks)
    )
    return ReconciliationReport(
        apply=not dry_run,
        trading_halted=any(issue.blocks_trading for issue in issues),
        mismatch_count=len(issues),
        issues=issues,
    )


def startup_recovery_report(*, snapshot: ReconciliationSnapshot) -> ReconciliationReport:
    return reconcile_snapshot(snapshot=snapshot, dry_run=True)


def _order_issues(*, snapshot: ReconciliationSnapshot) -> tuple[ReconciliationIssue, ...]:
    issues: tuple[ReconciliationIssue, ...] = ()
    local_open = _orders_by_id(snapshot.local.open_orders)
    exchange_open = _orders_by_id(snapshot.exchange.open_orders)
    exchange_closed = _orders_by_id(snapshot.exchange.closed_orders)
    for order_id in sorted(local_open.keys() - exchange_open.keys()):
        issues += (
            _issue(
                ReconciliationCode.ORPHAN_LOCAL_ORDER,
                order_id,
                "local open order is absent from exchange open orders",
            ),
        )
    for order_id in sorted(exchange_open.keys() - local_open.keys()):
        issues += (
            _issue(
                ReconciliationCode.ORPHAN_EXCHANGE_ORDER,
                order_id,
                "exchange open order is absent from local open orders",
            ),
        )
    for order_id in sorted(local_open.keys() & exchange_open.keys()):
        order = local_open[order_id]
        if order.pending_cancel:
            issues += (
                _issue(
                    ReconciliationCode.PENDING_CANCEL,
                    order_id,
                    "local order is pending cancel but exchange still reports it open",
                ),
            )
    for order in snapshot.local.closed_orders:
        if order.order_id not in exchange_closed:
            issues += (
                _issue(
                    ReconciliationCode.MISSING_EXCHANGE_FILL,
                    order.order_id,
                    "local filled order is missing from exchange closed orders",
                ),
            )
    return issues


def _position_issues(*, snapshot: ReconciliationSnapshot) -> tuple[ReconciliationIssue, ...]:
    issues: tuple[ReconciliationIssue, ...] = ()
    local_positions = _positions_by_key(snapshot.local.positions)
    exchange_positions = _positions_by_key(snapshot.exchange.positions)
    for key in sorted(local_positions.keys() | exchange_positions.keys()):
        local = local_positions.get(key)
        exchange = exchange_positions.get(key)
        subject = _position_subject(key)
        if local is None or exchange is None or local.quantity != exchange.quantity:
            issues += (
                _issue(
                    ReconciliationCode.POSITION_MISMATCH,
                    subject,
                    "local and exchange position size differ",
                ),
            )
        if local is not None and exchange is not None and local.leverage != exchange.leverage:
            issues += (
                _issue(
                    ReconciliationCode.LEVERAGE_MISMATCH,
                    subject,
                    "local and exchange leverage differ",
                ),
            )
        if local is not None and exchange is not None and local.margin_mode != exchange.margin_mode:
            issues += (
                _issue(
                    ReconciliationCode.MARGIN_MODE_MISMATCH,
                    subject,
                    "local and exchange margin mode differ",
                ),
            )
    return issues


def _balance_issues(*, snapshot: ReconciliationSnapshot) -> tuple[ReconciliationIssue, ...]:
    issues: tuple[ReconciliationIssue, ...] = ()
    local_balances = _balances_by_asset(snapshot.local.balances)
    exchange_balances = _balances_by_asset(snapshot.exchange.balances)
    for asset in sorted(local_balances.keys() | exchange_balances.keys()):
        local = local_balances.get(asset)
        exchange = exchange_balances.get(asset)
        if (
            local is None
            or exchange is None
            or local.total != exchange.total
            or local.available != exchange.available
        ):
            issues += (
                _issue(
                    ReconciliationCode.BALANCE_MISMATCH,
                    asset,
                    "local and exchange balances differ",
                ),
            )
    return issues


def _trade_issues(trades: tuple[TradeSnapshot, ...]) -> tuple[ReconciliationIssue, ...]:
    counts = Counter(trade.trade_id for trade in trades)
    return tuple(
        _issue(
            ReconciliationCode.DUPLICATE_LOCAL_TRADE,
            trade_id,
            "local trade id appears more than once",
        )
        for trade_id, count in sorted(counts.items())
        if count > 1
    )


def _lock_issues(locks: tuple[LockSnapshot, ...]) -> tuple[ReconciliationIssue, ...]:
    return tuple(
        _issue(ReconciliationCode.STALE_LOCK, lock.name, "local lock is stale")
        for lock in locks
        if lock.stale
    )


def _orders_by_id(orders: tuple[OrderSnapshot, ...]) -> OrderIndex:
    return {order.order_id: order for order in orders}


def _positions_by_key(
    positions: tuple[PositionSnapshot, ...],
) -> PositionIndex:
    return {(_position_key(position)): position for position in positions}


def _position_key(position: PositionSnapshot) -> PositionKey:
    return (position.pair, position.side.value)


def _position_subject(key: PositionKey) -> str:
    pair, side = key
    return f"{pair}:{side}"


def _balances_by_asset(balances: tuple[BalanceSnapshot, ...]) -> BalanceIndex:
    return {balance.asset: balance for balance in balances}


def _issue(
    code: ReconciliationCode,
    subject: str,
    message: str,
) -> ReconciliationIssue:
    return ReconciliationIssue(
        code=code,
        subject=subject,
        message=message,
        blocks_trading=True,
        suggested_action=f"dry-run: inspect {subject}; {message}",
    )
