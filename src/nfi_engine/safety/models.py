from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique


@unique
class SafetyWarningCode(StrEnum):
    FUTURES_ACCOUNT_EXCLUSIVITY = "FUTURES_ACCOUNT_EXCLUSIVITY"
    LEVERAGE_RISK = "LEVERAGE_RISK"
    CROSS_MARGIN_ACCOUNT_RISK = "CROSS_MARGIN_ACCOUNT_RISK"


@unique
class SafetyWarningSeverity(StrEnum):
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class SafetyWarning:
    code: SafetyWarningCode
    message: str
    severity: SafetyWarningSeverity = SafetyWarningSeverity.WARNING


@dataclass(frozen=True, slots=True)
class SafetyReport:
    warnings: tuple[SafetyWarning, ...]
