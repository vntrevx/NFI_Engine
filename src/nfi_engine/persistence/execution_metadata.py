from __future__ import annotations

import json
from typing import Final, assert_never

from pydantic import TypeAdapter

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]

MAX_EXECUTION_METADATA_BYTES: Final = 4096
REDACTED_METADATA_VALUE: Final = "***redacted***"
TRUNCATED_METADATA_JSON: Final = '{"metadata":"***redacted:metadata-too-large***"}'
SECRET_METADATA_TOKENS: Final = frozenset(
    (
        "api_key",
        "api_secret",
        "secret",
        "signature",
        "token",
        "password",
        "passphrase",
    ),
)
_JSON_VALUE_ADAPTER: Final[TypeAdapter[JsonValue]] = TypeAdapter[JsonValue](JsonValue)


def redacted_execution_metadata_json(metadata_json: str) -> str:
    parsed = _JSON_VALUE_ADAPTER.validate_json(metadata_json)
    encoded = json.dumps(
        _redact_json_value(parsed),
        separators=(",", ":"),
        sort_keys=True,
    )
    if len(encoded.encode()) <= MAX_EXECUTION_METADATA_BYTES:
        return encoded
    return TRUNCATED_METADATA_JSON


def _redact_json_value(value: JsonValue) -> JsonValue:
    match value:
        case dict():
            return {
                key: REDACTED_METADATA_VALUE
                if _is_secret_metadata_key(key)
                else _redact_json_value(item)
                for key, item in value.items()
            }
        case list():
            return [_redact_json_value(item) for item in value]
        case str() | int() | float() | bool() | None:
            return value
        case unreachable:
            assert_never(unreachable)


def _is_secret_metadata_key(key: str) -> bool:
    normalized = key.casefold().replace("-", "_")
    return any(token in normalized for token in SECRET_METADATA_TOKENS)
