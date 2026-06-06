from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from nfi_engine.plugins.errors import PluginError, PluginErrorCode


class StrictPluginModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


@unique
class PluginGroup(StrEnum):
    DATA = "data"
    EXCHANGE = "exchange"
    NOTIFIER = "notifier"
    RISK = "risk"
    STRATEGY = "strategy"


class PluginManifest(StrictPluginModel):
    name: str
    group: PluginGroup
    version: str
    engine_min_version: str
    entrypoint: str
    description: str


class RegisteredPlugin(StrictPluginModel):
    manifest: PluginManifest
    built_in: bool
    source: str

    @property
    def name(self) -> str:
        return self.manifest.name

    @property
    def group(self) -> PluginGroup:
        return self.manifest.group


@dataclass(frozen=True, slots=True)
class PluginRegistry:
    plugins: tuple[RegisteredPlugin, ...]

    def list_plugins(self) -> tuple[RegisteredPlugin, ...]:
        return self.plugins

    def inspect(self, *, name: str, group: PluginGroup) -> RegisteredPlugin:
        for plugin in self.plugins:
            if plugin.name == name and plugin.group is group:
                return plugin
        raise PluginError(
            code=PluginErrorCode.PLUGIN_NOT_FOUND,
            message=f"plugin not found: group={group.value} name={name}",
        )
