from __future__ import annotations

from pathlib import Path

import pytest

from nfi_engine.config import load_runtime_settings
from nfi_engine.config.models import RuntimeSettings
from nfi_engine.plugins import (
    PluginError,
    PluginErrorCode,
    PluginGroup,
    PluginManifest,
    build_plugin_registry,
)


def test_manifest_parses_known_group() -> None:
    # Given: an external data plugin manifest.
    raw_manifest = Path("tests/fixtures/plugins/extra-data/nfi-plugin.json").read_text(
        encoding="utf-8",
    )

    # When: the manifest is parsed at the trust boundary.
    manifest = PluginManifest.model_validate_json(raw_manifest)

    # Then: group and metadata become typed plugin values.
    assert manifest.group is PluginGroup.DATA
    assert manifest.name == "fixture-data-extra"


def test_builtin_registry_lists_required_groups_in_deterministic_order() -> None:
    # Given: default runtime settings with no external roots.
    settings = RuntimeSettings()

    # When: the registry is built.
    registry = build_plugin_registry(settings)
    plugins = registry.list_plugins()

    # Then: all milestone-one groups are present and sorted.
    assert tuple(plugin.group for plugin in plugins) == tuple(
        sorted((plugin.group for plugin in plugins), key=lambda group: group.value),
    )
    assert {plugin.group for plugin in plugins} >= {
        PluginGroup.STRATEGY,
        PluginGroup.EXCHANGE,
        PluginGroup.RISK,
        PluginGroup.NOTIFIER,
        PluginGroup.DATA,
    }


def test_duplicate_external_plugin_names_are_rejected() -> None:
    # Given: two configured plugin roots with the same group/name pair.
    settings = load_runtime_settings(Path("tests/fixtures/config/duplicate-plugin-root.yaml"))

    # When/Then: registry construction rejects the ambiguous plugin.
    with pytest.raises(PluginError) as exc_info:
        build_plugin_registry(settings)
    assert exc_info.value.code is PluginErrorCode.PLUGIN_DUPLICATE_NAME


def test_incompatible_external_plugin_version_is_rejected() -> None:
    # Given: a configured plugin requiring a future engine version.
    settings = load_runtime_settings(Path("tests/fixtures/config/incompatible-plugin-root.yaml"))

    # When/Then: registry construction rejects it before registration.
    with pytest.raises(PluginError) as exc_info:
        build_plugin_registry(settings)
    assert exc_info.value.code is PluginErrorCode.PLUGIN_INCOMPATIBLE_VERSION


def test_disabled_plugin_roots_skip_external_discovery() -> None:
    # Given: duplicate external roots with plugin discovery disabled.
    settings = load_runtime_settings(Path("tests/fixtures/config/disabled-plugin-roots.yaml"))

    # When: the registry is built.
    registry = build_plugin_registry(settings)

    # Then: built-ins still exist and duplicate external manifests are ignored.
    assert registry.inspect(name="simulator-exchange", group=PluginGroup.EXCHANGE).built_in is True


def test_builtin_plugin_can_be_inspected_by_group_and_name() -> None:
    # Given: the default built-in plugin registry.
    registry = build_plugin_registry(RuntimeSettings())

    # When: the simulator exchange plugin is inspected.
    plugin = registry.inspect(name="simulator-exchange", group=PluginGroup.EXCHANGE)

    # Then: typed metadata is returned for CLI/API surfaces.
    assert plugin.manifest.name == "simulator-exchange"
    assert plugin.manifest.group is PluginGroup.EXCHANGE
    assert plugin.built_in is True
