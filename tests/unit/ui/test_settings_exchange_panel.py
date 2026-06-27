from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

from nfi_engine.config.models import RuntimeSettings
from nfi_engine.exchange import ExchangeCapabilityProfile, ExchangeSupportLevel
from nfi_engine.exchange.official_requirement_models import ExchangeOfficialRequirement
from nfi_engine.ui.settings_exchange import render_exchange_registry_panel

if TYPE_CHECKING:
    import pytest


def test_exchange_registry_count_uses_required_official_profile_denominator(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _profile(exchange_id="checked", support_level=ExchangeSupportLevel.CANDIDATE)
    second = _profile(exchange_id="missing", support_level=ExchangeSupportLevel.CANDIDATE)
    generic = _profile(
        exchange_id="generic",
        support_level=ExchangeSupportLevel.GENERIC_UNVERIFIED,
    )

    def fake_requirement(exchange_id: str) -> ExchangeOfficialRequirement | None:
        if exchange_id == "checked":
            return ExchangeOfficialRequirement(
                exchange_id="checked",
                official_doc_url="https://example.invalid/docs",
                credential_fields=("api_key", "api_secret"),
                secret_fields=("api_secret",),
                identifier_fields=("api_key",),
                required_permissions=(),
                account_notes=(),
                testnet_notes=(),
                order_notes=(),
            )
        return None

    monkeypatch.setattr(
        "nfi_engine.ui.settings_exchange.list_exchange_profiles",
        lambda: (first, second, generic),
    )
    monkeypatch.setattr(
        "nfi_engine.ui.settings_exchange.get_official_requirement",
        fake_requirement,
    )

    html = render_exchange_registry_panel(
        settings=RuntimeSettings(),
        locale=RuntimeSettings().ui.locale,
    )

    assert 'data-testid="exchange-registry-count">0/3 verified | 1/2 official docs checked<' in html


def _profile(
    *,
    exchange_id: str,
    support_level: ExchangeSupportLevel,
) -> ExchangeCapabilityProfile:
    return ExchangeCapabilityProfile(
        exchange_id=exchange_id,
        display_name=exchange_id.title(),
        support_level=support_level,
        supports_spot=True,
        supports_futures=False,
        margin_modes=(),
        stoploss_order_types=(),
        supports_market_orders=False,
        supports_testnet=False,
        supports_sandbox=False,
        supports_trailing_stop=False,
        supports_data_only=True,
        credential_fields=(),
        evidence="test",
        checked_on=date(2026, 6, 25),
    )
