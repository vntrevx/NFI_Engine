from __future__ import annotations

from collections.abc import Iterable
from typing import Final

REDACTED_TEXT: Final = "REDACTED"


def redact_text(text: str, *, secrets: Iterable[str]) -> str:
    redacted = text
    for secret in secrets:
        if secret != "":
            redacted = redacted.replace(secret, REDACTED_TEXT)
    return redacted
