from __future__ import annotations

from typing import Final, Protocol

from nfi_engine.exchange.capabilities import get_exchange_profile
from nfi_engine.exchange.official_requirements import official_credential_fields

DEFAULT_CREDENTIAL_FIELDS: Final = ("api_key", "api_secret")


class _ExchangeCredentialSettings(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def api_key(self) -> str | None: ...

    @property
    def api_secret(self) -> str | None: ...

    @property
    def passphrase(self) -> str | None: ...

    @property
    def memo(self) -> str | None: ...

    @property
    def operator_id(self) -> str | None: ...

    @property
    def account_address(self) -> str | None: ...

    @property
    def api_wallet_signer(self) -> str | None: ...


class _RuntimeCredentialSettings(Protocol):
    @property
    def exchange(self) -> _ExchangeCredentialSettings: ...


def required_runtime_credential_fields(
    settings: _RuntimeCredentialSettings,
) -> tuple[str, ...]:
    profile = get_exchange_profile(settings.exchange.name)
    if profile is None:
        return DEFAULT_CREDENTIAL_FIELDS
    official_fields = official_credential_fields(profile.exchange_id)
    if official_fields is not None:
        return official_fields
    return profile.credential_fields


def missing_runtime_credential_fields(
    settings: _RuntimeCredentialSettings,
) -> tuple[str, ...]:
    return tuple(
        field
        for field in required_runtime_credential_fields(settings)
        if not _field_is_present(field, settings)
    )


def _field_is_present(field: str, settings: _RuntimeCredentialSettings) -> bool:
    match field:
        case "api_key":
            value = settings.exchange.api_key
        case "api_secret":
            value = settings.exchange.api_secret
        case "passphrase":
            value = settings.exchange.passphrase
        case "memo":
            value = settings.exchange.memo
        case "operator_id":
            value = settings.exchange.operator_id
        case "account_address":
            value = settings.exchange.account_address
        case "api_wallet_signer":
            value = settings.exchange.api_wallet_signer
        case _:
            value = None
    return _present(value)


def _present(value: str | None) -> bool:
    return value is not None and value.strip() != ""
