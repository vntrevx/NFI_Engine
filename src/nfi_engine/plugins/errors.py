from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from pathlib import Path
from typing import override


@unique
class PluginErrorCode(StrEnum):
    PLUGIN_DUPLICATE_NAME = "PLUGIN_DUPLICATE_NAME"
    PLUGIN_GROUP_NOT_ALLOWED = "PLUGIN_GROUP_NOT_ALLOWED"
    PLUGIN_INCOMPATIBLE_VERSION = "PLUGIN_INCOMPATIBLE_VERSION"
    PLUGIN_MANIFEST_INVALID = "PLUGIN_MANIFEST_INVALID"
    PLUGIN_MANIFEST_NOT_FOUND = "PLUGIN_MANIFEST_NOT_FOUND"
    PLUGIN_NOT_FOUND = "PLUGIN_NOT_FOUND"


@dataclass(frozen=True, slots=True)
class PluginError(Exception):
    code: PluginErrorCode
    message: str
    path: Path | None = None

    @override
    def __str__(self) -> str:
        if self.path is None:
            return f"{self.code.value}: {self.message}"
        return f"{self.code.value}: {self.message} path={self.path}"
