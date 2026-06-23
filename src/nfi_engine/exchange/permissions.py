from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import assert_never


@unique
class ExchangeApiPermissionState(StrEnum):
    ENABLED = "enabled"
    DISABLED = "disabled"
    UNKNOWN = "unknown"
    NOT_APPLICABLE = "not_applicable"


@dataclass(frozen=True, slots=True)
class ExchangeApiPermissionAudit:
    read: ExchangeApiPermissionState
    trade: ExchangeApiPermissionState
    futures: ExchangeApiPermissionState
    withdrawal: ExchangeApiPermissionState
    ip_allowlist: ExchangeApiPermissionState

    @property
    def live_safe(self) -> bool:
        return self.live_blocking_codes == ()

    @property
    def live_blocking_codes(self) -> tuple[str, ...]:
        match self.withdrawal:
            case ExchangeApiPermissionState.ENABLED:
                return ("EXCHANGE_WITHDRAWAL_PERMISSION_ENABLED",)
            case (
                ExchangeApiPermissionState.DISABLED
                | ExchangeApiPermissionState.UNKNOWN
                | ExchangeApiPermissionState.NOT_APPLICABLE
            ):
                return ()
            case unreachable:
                assert_never(unreachable)

    @property
    def diagnostic_codes(self) -> tuple[str, ...]:
        return _unknown_diagnostics(self.withdrawal, self.ip_allowlist)

    @property
    def summary(self) -> str:
        return (
            f"read={self.read.value} trade={self.trade.value} futures={self.futures.value} "
            f"withdrawal={self.withdrawal.value} ip_allowlist={self.ip_allowlist.value}"
        )


def audit_exchange_api_permissions(
    *,
    read: ExchangeApiPermissionState,
    trade: ExchangeApiPermissionState,
    futures: ExchangeApiPermissionState,
    withdrawal: ExchangeApiPermissionState,
    ip_allowlist: ExchangeApiPermissionState,
) -> ExchangeApiPermissionAudit:
    return ExchangeApiPermissionAudit(
        read=read,
        trade=trade,
        futures=futures,
        withdrawal=withdrawal,
        ip_allowlist=ip_allowlist,
    )


def _unknown_diagnostics(
    withdrawal: ExchangeApiPermissionState,
    ip_allowlist: ExchangeApiPermissionState,
) -> tuple[str, ...]:
    diagnostics: list[str] = []
    match withdrawal:
        case ExchangeApiPermissionState.UNKNOWN:
            diagnostics.append("EXCHANGE_PERMISSION_WITHDRAWAL_UNKNOWN")
        case (
            ExchangeApiPermissionState.ENABLED
            | ExchangeApiPermissionState.DISABLED
            | ExchangeApiPermissionState.NOT_APPLICABLE
        ):
            pass
        case unreachable:
            assert_never(unreachable)
    match ip_allowlist:
        case ExchangeApiPermissionState.UNKNOWN:
            pass
        case (
            ExchangeApiPermissionState.ENABLED
            | ExchangeApiPermissionState.DISABLED
            | ExchangeApiPermissionState.NOT_APPLICABLE
        ):
            pass
        case unreachable:
            assert_never(unreachable)
    return tuple(diagnostics)
