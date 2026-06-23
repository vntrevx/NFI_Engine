from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path
from typing import Final

from pydantic import ValidationError

from nfi_engine.config.enums import ConfigErrorCode
from nfi_engine.config.env_overrides import ConfigData, ConfigScalar, apply_env_overrides
from nfi_engine.config.errors import ConfigLoadError
from nfi_engine.config.models import RuntimeSettings
from nfi_engine.config.validators import validate_runtime_settings_model

MIN_QUOTED_SCALAR_LENGTH: Final = 2


def load_runtime_settings(path: Path) -> RuntimeSettings:
    raw_config = _read_yaml_config(path)
    config_with_env = apply_env_overrides(raw_config, os.environ)
    try:
        settings = RuntimeSettings.model_validate(config_with_env)
    except ValidationError as exc:
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_VALIDATION_FAILED,
            message=_format_validation_error(exc),
            path=path,
        ) from exc
    validate_runtime_settings(settings=settings, path=path)
    return settings


def validate_runtime_settings(*, settings: RuntimeSettings, path: Path) -> None:
    validate_runtime_settings_model(settings=settings, path=path)


def _read_yaml_config(path: Path) -> ConfigData:
    if not path.exists():
        raise ConfigLoadError(
            code=ConfigErrorCode.CONFIG_FILE_NOT_FOUND,
            message="config file does not exist",
            path=path,
        )
    return _parse_yaml_mapping(path.read_text(encoding="utf-8").splitlines(), path)


def _parse_yaml_mapping(lines: Iterable[str], path: Path) -> ConfigData:
    root: ConfigData = {}
    stack: list[tuple[int, ConfigData]] = [(-1, root)]
    for line_number, line in enumerate(lines, start=1):
        if _is_ignored_yaml_line(line):
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2 != 0:
            raise _yaml_error(
                path=path, line_number=line_number, message="indent must use two spaces"
            )
        key, raw_value = _parse_yaml_line(line=line, path=path, line_number=line_number)
        while indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if raw_value is None:
            nested: ConfigData = {}
            parent[key] = nested
            stack.append((indent, nested))
        else:
            parent[key] = _parse_scalar(raw_value)
    return root


def _is_ignored_yaml_line(line: str) -> bool:
    stripped = line.strip()
    return stripped == "" or stripped.startswith("#")


def _parse_yaml_line(*, line: str, path: Path, line_number: int) -> tuple[str, str | None]:
    stripped = line.strip()
    key, separator, value = stripped.partition(":")
    if separator == "" or key == "":
        raise _yaml_error(path=path, line_number=line_number, message="expected key: value")
    normalized_value = value.strip()
    if normalized_value == "":
        return key, None
    return key, normalized_value


def _parse_scalar(raw: str) -> ConfigScalar:
    unquoted = _unquote(raw)
    match unquoted.lower():
        case "null" | "~":
            return None
        case "true":
            return True
        case "false":
            return False
        case _:
            return unquoted


def _unquote(raw: str) -> str:
    if len(raw) >= MIN_QUOTED_SCALAR_LENGTH and raw[0] == raw[-1] and raw[0] in {"'", '"'}:
        return raw[1:-1]
    return raw


def _yaml_error(*, path: Path, line_number: int, message: str) -> ConfigLoadError:
    return ConfigLoadError(
        code=ConfigErrorCode.YAML_NOT_MAPPING,
        message=f"{message} at line {line_number}",
        path=path,
    )


def _format_validation_error(exc: ValidationError) -> str:
    return "; ".join(error["type"] for error in exc.errors())
