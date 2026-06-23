from __future__ import annotations

from decimal import Decimal

from nfi_engine.config.enums import RiskProfileName
from nfi_engine.risk.profiles import get_risk_profile


def test_balanced_risk_profile_uses_default_three_x_guardrails() -> None:
    # Given: the default operator risk profile.
    profile = get_risk_profile(RiskProfileName.BALANCED)

    # When: setup and preflight consume its guardrails.
    leverage = profile.leverage

    # Then: it maps to the agreed 3x default with bounded exposure.
    assert leverage == Decimal(3)
    assert profile.max_leverage == Decimal(3)
    assert profile.max_open_trades == 3
    assert profile.max_daily_loss_pct <= Decimal("0.05")
    assert profile.requires_confirmation is False


def test_expert_risk_profile_requires_explicit_confirmation() -> None:
    # Given: the highest-risk operator profile.
    profile = get_risk_profile(RiskProfileName.EXPERT)

    # When: its setup contract is inspected.
    requires_confirmation = profile.requires_confirmation

    # Then: callers must require an explicit expert confirmation gate.
    assert requires_confirmation is True
    assert profile.max_leverage > get_risk_profile(RiskProfileName.BALANCED).max_leverage


def test_safe_risk_profile_is_lower_exposure_than_balanced() -> None:
    # Given: safe and balanced profiles.
    safe = get_risk_profile(RiskProfileName.SAFE)
    balanced = get_risk_profile(RiskProfileName.BALANCED)

    # When: their exposure caps are compared.
    safe_exposure = safe.max_open_trades * safe.leverage
    balanced_exposure = balanced.max_open_trades * balanced.leverage

    # Then: safe keeps strictly lower notional pressure.
    assert safe_exposure < balanced_exposure
    assert safe.max_daily_loss_pct < balanced.max_daily_loss_pct
