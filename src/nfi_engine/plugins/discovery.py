from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import assert_never

from pydantic import ValidationError

from nfi_engine import __version__
from nfi_engine.plugins.errors import PluginError, PluginErrorCode
from nfi_engine.plugins.models import PluginGroup, PluginManifest, RegisteredPlugin

MANIFEST_FILE = "nfi-plugin.json"


@dataclass(frozen=True, order=True, slots=True)
class VersionParts:
    major: int
    minor: int
    patch: int


def discover_external_plugins(
    *,
    roots: tuple[Path, ...],
    allowed_groups: tuple[PluginGroup, ...],
) -> tuple[RegisteredPlugin, ...]:
    return tuple(
        _registered_from_manifest(_load_manifest(root), root=root, allowed_groups=allowed_groups)
        for root in sorted(roots)
    )


def parse_plugin_roots(raw_roots: str) -> tuple[Path, ...]:
    return tuple(Path(item.strip()) for item in raw_roots.split(",") if item.strip() != "")


def parse_allowed_groups(raw_groups: str) -> tuple[PluginGroup, ...]:
    return tuple(_parse_group(item.strip()) for item in raw_groups.split(",") if item.strip() != "")


def _parse_group(raw: str) -> PluginGroup:
    try:
        return PluginGroup(raw)
    except ValueError as exc:
        raise PluginError(
            code=PluginErrorCode.PLUGIN_GROUP_NOT_ALLOWED,
            message=f"plugin group is not allowed: {raw}",
        ) from exc


def _load_manifest(root: Path) -> PluginManifest:
    manifest_path = root / MANIFEST_FILE
    if not manifest_path.exists():
        raise PluginError(
            code=PluginErrorCode.PLUGIN_MANIFEST_NOT_FOUND,
            message="plugin manifest not found",
            path=manifest_path,
        )
    try:
        return PluginManifest.model_validate_json(manifest_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, ValidationError) as exc:
        raise PluginError(
            code=PluginErrorCode.PLUGIN_MANIFEST_INVALID,
            message=str(exc),
            path=manifest_path,
        ) from exc


def _registered_from_manifest(
    manifest: PluginManifest,
    *,
    root: Path,
    allowed_groups: tuple[PluginGroup, ...],
) -> RegisteredPlugin:
    if manifest.group not in allowed_groups:
        raise PluginError(
            code=PluginErrorCode.PLUGIN_GROUP_NOT_ALLOWED,
            message=f"plugin group is not allowlisted: {manifest.group.value}",
            path=root,
        )
    if _parse_version(manifest.engine_min_version) > _parse_version(__version__):
        raise PluginError(
            code=PluginErrorCode.PLUGIN_INCOMPATIBLE_VERSION,
            message=(
                f"plugin {manifest.name} requires engine>={manifest.engine_min_version}; "
                f"current={__version__}"
            ),
            path=root,
        )
    return RegisteredPlugin(manifest=manifest, built_in=False, source=str(root))


def _parse_version(raw: str) -> VersionParts:
    parts = raw.split(".")
    match parts:
        case [major, minor, patch]:
            try:
                return VersionParts(major=int(major), minor=int(minor), patch=int(patch))
            except ValueError as exc:
                raise PluginError(
                    code=PluginErrorCode.PLUGIN_MANIFEST_INVALID,
                    message=f"invalid semantic version: {raw}",
                ) from exc
        case _:
            raise PluginError(
                code=PluginErrorCode.PLUGIN_MANIFEST_INVALID,
                message=f"invalid semantic version: {raw}",
            )
    assert_never(parts)
