from __future__ import annotations

from enum import StrEnum, auto, unique
from typing import ClassVar, override

from pydantic import BaseModel, ConfigDict


class UpperStrEnum(StrEnum):
    @staticmethod
    @override
    def _generate_next_value_(
        name: str,
        start: int,
        count: int,
        last_values: list[str],
    ) -> str:
        del start, count, last_values
        return name


@unique
class PreflightStatus(UpperStrEnum):
    PASS = auto()
    WARN = auto()
    BLOCK = auto()


@unique
class PreflightCode(UpperStrEnum):
    CONFIG_VALID = auto()
    CONFIG_INVALID = auto()
    PROFILE_COMPATIBLE = auto()
    PROFILE_CONFIG_MISMATCH = auto()
    PUBLIC_BIND_NOT_ALLOWED = auto()
    WEAK_API_TOKEN = auto()
    LIVE_TRADING_DISABLED = auto()
    LIVE_TRADING_OUT_OF_SCOPE = auto()
    LIVE_EXCHANGE_CREDENTIALS = auto()
    LIVE_PERMISSION_HARDENING = auto()
    LIVE_RECONCILIATION_HARDENING = auto()
    LIVE_CIRCUIT_BREAKER_HARDENING = auto()
    LIVE_STRATEGY_HARDENING = auto()
    FUTURES_LEVERAGE_INVALID = auto()
    EXCHANGE_PERMISSION_AUDIT = auto()
    RISK_PROFILE_GUARDRAILS = auto()
    EXCHANGE_TESTNET_REQUIRED = auto()
    DB_PATH_READY = auto()
    DB_PATH_MISSING = auto()
    LOG_PATH_READY = auto()
    LOG_PATH_NOT_WRITABLE = auto()
    DOCKER_VOLUMES_READY = auto()
    DOCKER_VOLUMES_MISSING = auto()
    NOTIFIER_DRY_RUN_READY = auto()
    NOTIFIER_DISABLED = auto()
    PAIR_CONFIG_VALID = auto()
    RECONCILIATION_READY = auto()
    RECONCILIATION_REQUIRED = auto()


class StrictPreflightModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


class PreflightCheck(StrictPreflightModel):
    code: PreflightCode
    status: PreflightStatus
    message: str


class PreflightReport(StrictPreflightModel):
    profile: str
    blocked: bool
    checks: tuple[PreflightCheck, ...]
