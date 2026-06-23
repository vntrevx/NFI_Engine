from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from nfi_engine.api.models import StrictApiModel
from nfi_engine.wallet import WalletBalanceSnapshot, WalletPermissionAuditSnapshot


class WalletPermissionAuditResponse(StrictApiModel):
    read: str
    trade: str
    futures: str
    withdrawal: str
    ip_allowlist: str
    live_safe: bool
    live_blocking_codes: tuple[str, ...]
    diagnostic_codes: tuple[str, ...]
    summary: str

    @classmethod
    def from_snapshot(
        cls,
        snapshot: WalletPermissionAuditSnapshot,
    ) -> WalletPermissionAuditResponse:
        return cls(
            read=snapshot.read.value,
            trade=snapshot.trade.value,
            futures=snapshot.futures.value,
            withdrawal=snapshot.withdrawal.value,
            ip_allowlist=snapshot.ip_allowlist.value,
            live_safe=snapshot.live_safe,
            live_blocking_codes=snapshot.live_blocking_codes,
            diagnostic_codes=snapshot.diagnostic_codes,
            summary=snapshot.summary,
        )


class WalletBalanceResponse(StrictApiModel):
    status: str
    code: str
    exchange: str
    trading_mode: str
    captured_at: str | None
    equity: str | None
    available: str | None
    quote_asset: str
    position_count: int
    allocation_cap_pct: str
    allocation_cap: str | None
    configured_stake_usdt: str
    configured_max_open_trades: int
    configured_allocation_total: str
    allocation_cap_exceeded: bool | None
    permission_audit: WalletPermissionAuditResponse
    next_action: str
    message: str

    @classmethod
    def from_snapshot(cls, snapshot: WalletBalanceSnapshot) -> WalletBalanceResponse:
        return cls(
            status=snapshot.status.value,
            code=snapshot.code.value,
            exchange=snapshot.exchange,
            trading_mode=snapshot.trading_mode,
            captured_at=(
                None if snapshot.captured_at is None else _datetime_json(snapshot.captured_at)
            ),
            equity=None if snapshot.equity is None else _decimal_json(snapshot.equity),
            available=None if snapshot.available is None else _decimal_json(snapshot.available),
            quote_asset=snapshot.quote_asset,
            position_count=snapshot.position_count,
            allocation_cap_pct=_decimal_json(snapshot.allocation_cap_pct),
            allocation_cap=(
                None if snapshot.allocation_cap is None else _decimal_json(snapshot.allocation_cap)
            ),
            configured_stake_usdt=_decimal_json(snapshot.configured_stake_usdt),
            configured_max_open_trades=snapshot.configured_max_open_trades,
            configured_allocation_total=_decimal_json(snapshot.configured_allocation_total),
            allocation_cap_exceeded=snapshot.allocation_cap_exceeded,
            permission_audit=WalletPermissionAuditResponse.from_snapshot(
                snapshot.permission_audit,
            ),
            next_action=snapshot.next_action,
            message=snapshot.message,
        )


def _datetime_json(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decimal_json(value: Decimal) -> str:
    return str(value)
