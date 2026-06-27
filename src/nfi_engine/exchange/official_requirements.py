from __future__ import annotations

from typing import Final

from nfi_engine.exchange.official_requirement_models import (
    ExchangeOfficialRequirement,
    OfficialRequirementPayload,
)
from nfi_engine.exchange.official_requirement_profiles_primary import (
    PRIMARY_OFFICIAL_REQUIREMENTS,
)
from nfi_engine.exchange.official_requirement_profiles_secondary import (
    SECONDARY_OFFICIAL_REQUIREMENTS,
)

OFFICIAL_REQUIREMENTS: Final = (
    *PRIMARY_OFFICIAL_REQUIREMENTS,
    *SECONDARY_OFFICIAL_REQUIREMENTS,
)

_OFFICIAL_REQUIREMENTS_BY_ID: Final = {
    requirement.exchange_id: requirement for requirement in OFFICIAL_REQUIREMENTS
}


def get_official_requirement(exchange_id: str) -> ExchangeOfficialRequirement | None:
    return _OFFICIAL_REQUIREMENTS_BY_ID.get(exchange_id)


def official_credential_fields(exchange_id: str) -> tuple[str, ...] | None:
    requirement = get_official_requirement(exchange_id)
    if requirement is None:
        return None
    return requirement.credential_fields


def list_official_requirements() -> tuple[ExchangeOfficialRequirement, ...]:
    return OFFICIAL_REQUIREMENTS


def build_official_requirement_payload(exchange_id: str) -> OfficialRequirementPayload:
    requirement = get_official_requirement(exchange_id)
    if requirement is None:
        return {
            "official_docs_checked": False,
            "official_doc_url": "",
            "official_docs_checked_on": "",
            "official_credential_fields": [],
            "official_secret_fields": [],
            "official_identifier_fields": [],
            "official_required_permissions": [],
            "official_account_notes": [],
            "official_testnet_notes": [],
            "official_order_notes": [],
        }
    return {
        "official_docs_checked": True,
        "official_doc_url": requirement.official_doc_url,
        "official_docs_checked_on": requirement.checked_on.isoformat(),
        "official_credential_fields": list(requirement.credential_fields),
        "official_secret_fields": list(requirement.secret_fields),
        "official_identifier_fields": list(requirement.identifier_fields),
        "official_required_permissions": list(requirement.required_permissions),
        "official_account_notes": list(requirement.account_notes),
        "official_testnet_notes": list(requirement.testnet_notes),
        "official_order_notes": list(requirement.order_notes),
    }
