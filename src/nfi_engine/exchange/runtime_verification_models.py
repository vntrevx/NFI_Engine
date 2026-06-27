from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import TypedDict, assert_never

from nfi_engine.domain import TradingMode
from nfi_engine.exchange.capability_models import (
    ExchangeCapabilityProfile,
    ExchangeSupportLevel,
)


@unique
class ExchangeRuntimeCheckStatus(StrEnum):
    PASS = "pass"  # noqa: S105 - runtime check status label, not a secret.
    BLOCK = "block"
    MANUAL = "manual"
    NOT_REQUIRED = "not-required"


class ExchangeRuntimeCheckPayload(TypedDict):
    stage: str
    status: str
    code: str
    message: str
    next_action: str


class ExchangeRuntimeReportPayload(TypedDict):
    exchange_id: str
    requested_exchange: str
    display_name: str
    support_level: str
    trading_mode: str
    runtime_verified: bool
    promotion_ready: bool
    blockers: list[str]
    checks: list[ExchangeRuntimeCheckPayload]


class ExchangeRuntimeReportCollectionPayload(TypedDict):
    reports: list[ExchangeRuntimeReportPayload]


@dataclass(frozen=True, slots=True)
class ExchangeRuntimeCheck:
    stage: str
    status: ExchangeRuntimeCheckStatus
    code: str
    message: str
    next_action: str

    def to_payload(self) -> ExchangeRuntimeCheckPayload:
        return {
            "stage": self.stage,
            "status": self.status.value,
            "code": self.code,
            "message": self.message,
            "next_action": self.next_action,
        }


@dataclass(frozen=True, slots=True)
class ExchangeRuntimeReport:
    requested_exchange: str
    profile: ExchangeCapabilityProfile
    trading_mode: TradingMode
    checks: tuple[ExchangeRuntimeCheck, ...]

    @property
    def exchange_id(self) -> str:
        return self.profile.exchange_id

    @property
    def runtime_verified(self) -> bool:
        return self.profile.support_level is ExchangeSupportLevel.VERIFIED

    @property
    def promotion_ready(self) -> bool:
        return self.runtime_verified and all(_check_is_closed(check) for check in self.checks)

    @property
    def blockers(self) -> tuple[str, ...]:
        return tuple(
            check.code for check in self.checks if check.status is ExchangeRuntimeCheckStatus.BLOCK
        )

    def to_payload(self) -> ExchangeRuntimeReportPayload:
        return {
            "exchange_id": self.profile.exchange_id,
            "requested_exchange": self.requested_exchange,
            "display_name": self.profile.display_name,
            "support_level": self.profile.support_level.value,
            "trading_mode": self.trading_mode.value,
            "runtime_verified": self.runtime_verified,
            "promotion_ready": self.promotion_ready,
            "blockers": list(self.blockers),
            "checks": [check.to_payload() for check in self.checks],
        }


def _check_is_closed(check: ExchangeRuntimeCheck) -> bool:
    match check.status:
        case ExchangeRuntimeCheckStatus.PASS | ExchangeRuntimeCheckStatus.NOT_REQUIRED:
            return True
        case ExchangeRuntimeCheckStatus.BLOCK | ExchangeRuntimeCheckStatus.MANUAL:
            return False
        case unreachable:
            assert_never(unreachable)
