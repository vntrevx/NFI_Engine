from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import override

from nfi_engine.config.enums import ConfigErrorCode


@dataclass(frozen=True, slots=True)
class ConfigLoadError(Exception):
    code: ConfigErrorCode
    message: str
    path: Path | None = None

    @override
    def __str__(self) -> str:
        if self.path is None:
            return f"{self.code.value}: {self.message}"
        return f"{self.code.value}: {self.message} path={self.path}"
