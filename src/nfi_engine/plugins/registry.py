from __future__ import annotations

from nfi_engine.config import RuntimeSettings
from nfi_engine.plugins.builtins import builtin_plugins
from nfi_engine.plugins.discovery import (
    discover_external_plugins,
    parse_allowed_groups,
    parse_plugin_roots,
)
from nfi_engine.plugins.errors import PluginError, PluginErrorCode
from nfi_engine.plugins.models import PluginGroup, PluginRegistry, RegisteredPlugin

type PluginKey = tuple[PluginGroup, str]


def build_plugin_registry(settings: RuntimeSettings) -> PluginRegistry:
    plugins = builtin_plugins()
    if settings.plugins.enabled:
        plugins += discover_external_plugins(
            roots=parse_plugin_roots(settings.plugins.roots),
            allowed_groups=parse_allowed_groups(settings.plugins.allow_groups),
        )
    return PluginRegistry(plugins=_sorted_plugins(_ensure_unique(plugins)))


def _ensure_unique(plugins: tuple[RegisteredPlugin, ...]) -> tuple[RegisteredPlugin, ...]:
    seen: set[PluginKey] = set()
    for plugin in plugins:
        key = (plugin.group, plugin.name)
        if key in seen:
            raise PluginError(
                code=PluginErrorCode.PLUGIN_DUPLICATE_NAME,
                message=f"duplicate plugin: group={plugin.group.value} name={plugin.name}",
            )
        seen.add(key)
    return plugins


def _sorted_plugins(plugins: tuple[RegisteredPlugin, ...]) -> tuple[RegisteredPlugin, ...]:
    return tuple(sorted(plugins, key=lambda plugin: (plugin.group.value, plugin.name)))
