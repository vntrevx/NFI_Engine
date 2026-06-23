from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import assert_never

from nfi_engine.config.enums import RiskProfileName


@dataclass(frozen=True, slots=True)
class RiskProfile:
    name: RiskProfileName
    stake_usdt: Decimal
    leverage: Decimal
    max_leverage: Decimal
    max_open_trades: int
    max_daily_loss_pct: Decimal
    allocation_cap_pct: Decimal
    requires_confirmation: bool


def get_risk_profile(name: RiskProfileName) -> RiskProfile:
    match name:
        case RiskProfileName.SAFE:
            return RiskProfile(
                name=name,
                stake_usdt=Decimal(10),
                leverage=Decimal(1),
                max_leverage=Decimal(1),
                max_open_trades=2,
                max_daily_loss_pct=Decimal("0.02"),
                allocation_cap_pct=Decimal("0.10"),
                requires_confirmation=False,
            )
        case RiskProfileName.BALANCED:
            return RiskProfile(
                name=name,
                stake_usdt=Decimal(25),
                leverage=Decimal(3),
                max_leverage=Decimal(3),
                max_open_trades=3,
                max_daily_loss_pct=Decimal("0.05"),
                allocation_cap_pct=Decimal("0.25"),
                requires_confirmation=False,
            )
        case RiskProfileName.EXPERT:
            return RiskProfile(
                name=name,
                stake_usdt=Decimal(50),
                leverage=Decimal(5),
                max_leverage=Decimal(5),
                max_open_trades=5,
                max_daily_loss_pct=Decimal("0.08"),
                allocation_cap_pct=Decimal("0.50"),
                requires_confirmation=True,
            )
        case unreachable:
            assert_never(unreachable)
