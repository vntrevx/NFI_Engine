from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated, ClassVar, Final, NoReturn

import typer
from pydantic import BaseModel, ConfigDict

from nfi_engine.config import ConfigLoadError, load_runtime_settings
from nfi_engine.plugins import PluginError, PluginGroup, RegisteredPlugin, build_plugin_registry

plugins_app: Final[typer.Typer] = typer.Typer(help="Inspect plugin registry contracts.")


class PluginCliResponse(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    group: str
    version: str
    engine_min_version: str
    entrypoint: str
    description: str
    built_in: bool
    source: str


@plugins_app.command("list")
def list_plugins(
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
) -> None:
    try:
        settings = load_runtime_settings(config)
        registry = build_plugin_registry(settings)
    except ConfigLoadError as exc:
        _exit_with_config_error(exc)
    except PluginError as exc:
        _exit_with_plugin_error(exc)
    for plugin in registry.list_plugins():
        sys.stdout.write(_format_plugin_line(plugin))
        sys.stdout.write("\n")


@plugins_app.command("inspect")
def inspect_plugin(
    name: Annotated[str, typer.Option("--name")],
    group: Annotated[PluginGroup, typer.Option("--group")],
    as_json: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        settings = load_runtime_settings(Path("examples/futures-paper.yaml"))
        plugin = build_plugin_registry(settings).inspect(name=name, group=group)
    except ConfigLoadError as exc:
        _exit_with_config_error(exc)
    except PluginError as exc:
        _exit_with_plugin_error(exc)
    payload = _plugin_payload(plugin)
    if as_json:
        sys.stdout.write(payload.model_dump_json())
        sys.stdout.write("\n")
        return
    sys.stdout.write(_format_payload(payload))
    sys.stdout.write("\n")


def _plugin_payload(plugin: RegisteredPlugin) -> PluginCliResponse:
    manifest = plugin.manifest
    return PluginCliResponse(
        name=manifest.name,
        group=manifest.group.value,
        version=manifest.version,
        engine_min_version=manifest.engine_min_version,
        entrypoint=manifest.entrypoint,
        description=manifest.description,
        built_in=plugin.built_in,
        source=plugin.source,
    )


def _format_plugin_line(plugin: RegisteredPlugin) -> str:
    payload = _plugin_payload(plugin)
    return (
        f"group={payload.group} name={payload.name} version={payload.version} "
        f"built_in={str(payload.built_in).lower()}"
    )


def _format_payload(payload: PluginCliResponse) -> str:
    return "\n".join(
        (
            f"name={payload.name}",
            f"group={payload.group}",
            f"version={payload.version}",
            f"engine_min_version={payload.engine_min_version}",
            f"entrypoint={payload.entrypoint}",
            f"built_in={str(payload.built_in).lower()}",
            f"source={payload.source}",
        ),
    )


def _exit_with_config_error(exc: ConfigLoadError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc


def _exit_with_plugin_error(exc: PluginError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc
