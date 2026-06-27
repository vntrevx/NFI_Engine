from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Final, TypedDict

OFFICIAL_REQUIREMENTS_CHECKED_ON: Final = date(2026, 6, 25)


@dataclass(frozen=True, slots=True)
class ExchangeOfficialRequirement:
    exchange_id: str
    official_doc_url: str
    credential_fields: tuple[str, ...]
    secret_fields: tuple[str, ...]
    identifier_fields: tuple[str, ...]
    required_permissions: tuple[str, ...]
    account_notes: tuple[str, ...]
    testnet_notes: tuple[str, ...]
    order_notes: tuple[str, ...]
    checked_on: date = OFFICIAL_REQUIREMENTS_CHECKED_ON


class OfficialRequirementPayload(TypedDict):
    official_docs_checked: bool
    official_doc_url: str
    official_docs_checked_on: str
    official_credential_fields: list[str]
    official_secret_fields: list[str]
    official_identifier_fields: list[str]
    official_required_permissions: list[str]
    official_account_notes: list[str]
    official_testnet_notes: list[str]
    official_order_notes: list[str]
