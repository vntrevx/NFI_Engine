from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum, unique

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import AccountSnapshot
from nfi_engine.exchange.permissions import (
    ExchangeApiPermissionState,
    audit_exchange_api_permissions,
)


@unique
class WalletBalanceStatus(StrEnum):
    FETCHED = "fetched"
    BLOCKED = "blocked"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


@unique
class WalletBalanceCode(StrEnum):
    FETCHED = "WALLET_BALANCE_FETCHED"
    MISSING_CREDENTIALS = "WALLET_BALANCE_MISSING_CREDENTIALS"
    UNSAFE_PERMISSION = "WALLET_BALANCE_UNSAFE_PERMISSION"
    ADAPTER_UNAVAILABLE = "WALLET_BALANCE_ADAPTER_UNAVAILABLE"
    TIMEOUT = "WALLET_BALANCE_TIMEOUT"
    EXCHANGE_ERROR = "WALLET_BALANCE_EXCHANGE_ERROR"


@dataclass(frozen=True, slots=True)
class WalletPermissionAuditSnapshot:
    read: ExchangeApiPermissionState
    trade: ExchangeApiPermissionState
    futures: ExchangeApiPermissionState
    withdrawal: ExchangeApiPermissionState
    ip_allowlist: ExchangeApiPermissionState
    live_safe: bool
    live_blocking_codes: tuple[str, ...]
    diagnostic_codes: tuple[str, ...]
    summary: str

    @classmethod
    def from_settings(cls, settings: RuntimeSettings) -> WalletPermissionAuditSnapshot:
        audit = audit_exchange_api_permissions(
            read=settings.exchange.permission_read,
            trade=settings.exchange.permission_trade,
            futures=settings.exchange.permission_futures,
            withdrawal=settings.exchange.permission_withdrawal,
            ip_allowlist=settings.exchange.permission_ip_allowlist,
        )
        return cls(
            read=audit.read,
            trade=audit.trade,
            futures=audit.futures,
            withdrawal=audit.withdrawal,
            ip_allowlist=audit.ip_allowlist,
            live_safe=audit.live_safe,
            live_blocking_codes=audit.live_blocking_codes,
            diagnostic_codes=audit.diagnostic_codes,
            summary=audit.summary,
        )

    @classmethod
    def unknown(cls) -> WalletPermissionAuditSnapshot:
        return cls(
            read=ExchangeApiPermissionState.UNKNOWN,
            trade=ExchangeApiPermissionState.UNKNOWN,
            futures=ExchangeApiPermissionState.UNKNOWN,
            withdrawal=ExchangeApiPermissionState.UNKNOWN,
            ip_allowlist=ExchangeApiPermissionState.UNKNOWN,
            live_safe=True,
            live_blocking_codes=(),
            diagnostic_codes=("EXCHANGE_PERMISSION_WITHDRAWAL_UNKNOWN",),
            summary=(
                "read=unknown trade=unknown futures=unknown withdrawal=unknown ip_allowlist=unknown"
            ),
        )


@dataclass(frozen=True, slots=True)
class WalletBalanceSnapshot:
    status: WalletBalanceStatus
    code: WalletBalanceCode
    exchange: str
    trading_mode: str
    captured_at: datetime | None
    equity: Decimal | None
    available: Decimal | None
    quote_asset: str
    position_count: int
    next_action: str
    message: str
    allocation_cap_pct: Decimal = Decimal(0)
    allocation_cap: Decimal | None = None
    configured_stake_usdt: Decimal = Decimal(0)
    configured_max_open_trades: int = 0
    configured_allocation_total: Decimal = Decimal(0)
    allocation_cap_exceeded: bool | None = None
    permission_audit: WalletPermissionAuditSnapshot = field(
        default_factory=WalletPermissionAuditSnapshot.unknown,
    )

    @classmethod
    def from_account(
        cls,
        *,
        settings: RuntimeSettings,
        account: AccountSnapshot,
    ) -> WalletBalanceSnapshot:
        available = Decimal(str(account.available))
        allocation_cap = _allocation_cap(settings=settings, available=available)
        configured_total = _configured_allocation_total(settings)
        return cls(
            status=WalletBalanceStatus.FETCHED,
            code=WalletBalanceCode.FETCHED,
            exchange=settings.exchange.name,
            trading_mode=settings.exchange.trading_mode.value,
            captured_at=account.captured_at,
            equity=Decimal(str(account.equity)),
            available=available,
            quote_asset=settings.pairlist.quote_asset,
            position_count=len(account.positions),
            next_action="Review allocation amount before enabling a run.",
            message="Wallet balance fetched through the exchange adapter boundary.",
            allocation_cap_pct=settings.risk.allocation_cap_pct,
            allocation_cap=allocation_cap,
            configured_stake_usdt=settings.risk.stake_usdt,
            configured_max_open_trades=settings.risk.max_open_trades,
            configured_allocation_total=configured_total,
            allocation_cap_exceeded=_allocation_cap_exceeded(
                allocation_cap=allocation_cap,
                configured_total=configured_total,
            ),
            permission_audit=WalletPermissionAuditSnapshot.from_settings(settings),
        )

    @classmethod
    def diagnostic(
        cls,
        *,
        settings: RuntimeSettings,
        status: WalletBalanceStatus,
        code: WalletBalanceCode,
        next_action: str,
        message: str,
    ) -> WalletBalanceSnapshot:
        return cls(
            status=status,
            code=code,
            exchange=settings.exchange.name,
            trading_mode=settings.exchange.trading_mode.value,
            captured_at=None,
            equity=None,
            available=None,
            quote_asset=settings.pairlist.quote_asset,
            position_count=0,
            next_action=next_action,
            message=message,
            allocation_cap_pct=settings.risk.allocation_cap_pct,
            configured_stake_usdt=settings.risk.stake_usdt,
            configured_max_open_trades=settings.risk.max_open_trades,
            configured_allocation_total=_configured_allocation_total(settings),
            permission_audit=WalletPermissionAuditSnapshot.from_settings(settings),
        )


def _allocation_cap(*, settings: RuntimeSettings, available: Decimal) -> Decimal:
    return available * settings.risk.allocation_cap_pct


def _configured_allocation_total(settings: RuntimeSettings) -> Decimal:
    return settings.risk.stake_usdt * Decimal(settings.risk.max_open_trades)


def _allocation_cap_exceeded(
    *,
    allocation_cap: Decimal | None,
    configured_total: Decimal,
) -> bool | None:
    if allocation_cap is None:
        return None
    return configured_total > allocation_cap
