from __future__ import annotations

import stat
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Final, override

_CREDENTIAL_FIELDS: Final = (
    "api_key",
    "api_secret",
    "passphrase",
    "memo",
    "operator_id",
    "account_address",
    "api_wallet_signer",
)

_FIELD_ALIASES: Final[Mapping[str, str]] = MappingProxyType(
    {
        "api_key": "api_key",
        "api_secret": "api_secret",
        "passphrase": "passphrase",
        "memo": "memo",
        "operator_id": "operator_id",
        "account_address": "account_address",
        "api_wallet_signer": "api_wallet_signer",
        "NFI_ENGINE_SETUP_API_KEY": "api_key",
        "NFI_ENGINE_SETUP_API_SECRET": "api_secret",
        "NFI_ENGINE_SETUP_PASSPHRASE": "passphrase",
        "NFI_ENGINE_SETUP_MEMO": "memo",
        "NFI_ENGINE_SETUP_OPERATOR_ID": "operator_id",
        "NFI_ENGINE_SETUP_ACCOUNT_ADDRESS": "account_address",
        "NFI_ENGINE_SETUP_API_WALLET_SIGNER": "api_wallet_signer",
    },
)


@dataclass(frozen=True, slots=True)
class SetupCredentialFileError(Exception):
    code: str
    message: str

    @override
    def __str__(self) -> str:
        return f"{self.code}: {self.message}"


@dataclass(frozen=True, slots=True)
class SetupCredentialValues:
    api_key: str = ""
    api_secret: str = ""
    passphrase: str = ""
    memo: str = ""
    operator_id: str = ""
    account_address: str = ""
    api_wallet_signer: str = ""


def load_setup_credentials_file(path: Path) -> SetupCredentialValues:
    _assert_secure_file(path)
    fields = _parse_credentials(path.read_text(encoding="utf-8"))
    return SetupCredentialValues(
        api_key=fields["api_key"],
        api_secret=fields["api_secret"],
        passphrase=fields["passphrase"],
        memo=fields["memo"],
        operator_id=fields["operator_id"],
        account_address=fields["account_address"],
        api_wallet_signer=fields["api_wallet_signer"],
    )


def _assert_secure_file(path: Path) -> None:
    try:
        file_stat = path.stat()
    except FileNotFoundError as exc:
        raise SetupCredentialFileError(
            code="SETUP_CREDENTIALS_FILE_NOT_FOUND",
            message="credentials file does not exist",
        ) from exc
    if not path.is_file():
        raise SetupCredentialFileError(
            code="SETUP_CREDENTIALS_FILE_NOT_FILE",
            message="credentials path must be a file",
        )
    mode = stat.S_IMODE(file_stat.st_mode)
    if mode & 0o077:
        raise SetupCredentialFileError(
            code="SETUP_CREDENTIALS_FILE_UNSAFE_MODE",
            message="credentials file must be readable only by its owner",
        )


def _parse_credentials(text: str) -> dict[str, str]:
    fields: dict[str, str] = dict.fromkeys(_CREDENTIAL_FIELDS, "")
    seen: set[str] = set()
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if line == "" or line.startswith("#"):
            continue
        key, value = _parse_line(line=line, line_number=line_number)
        field = _field_name(key=key, line_number=line_number)
        if field in seen:
            raise SetupCredentialFileError(
                code="SETUP_CREDENTIALS_FILE_DUPLICATE_FIELD",
                message=f"duplicate credential field on line {line_number}",
            )
        seen.add(field)
        fields[field] = value
    return fields


def _parse_line(*, line: str, line_number: int) -> tuple[str, str]:
    if "=" not in line:
        raise SetupCredentialFileError(
            code="SETUP_CREDENTIALS_FILE_INVALID_LINE",
            message=f"expected key=value on line {line_number}",
        )
    key, value = line.split("=", 1)
    normalized_key = key.strip()
    normalized_value = value.strip()
    if normalized_key == "":
        raise SetupCredentialFileError(
            code="SETUP_CREDENTIALS_FILE_INVALID_FIELD",
            message=f"empty credential field on line {line_number}",
        )
    return normalized_key, normalized_value


def _field_name(*, key: str, line_number: int) -> str:
    field = _FIELD_ALIASES.get(key)
    if field is None:
        raise SetupCredentialFileError(
            code="SETUP_CREDENTIALS_FILE_UNKNOWN_FIELD",
            message=f"unknown credential field on line {line_number}",
        )
    return field
