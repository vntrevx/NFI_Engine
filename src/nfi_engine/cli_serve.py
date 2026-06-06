from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Annotated, Final, NoReturn

import typer
import uvicorn

from nfi_engine.api.errors import ApiConfigurationError
from nfi_engine.api.settings import CONFIG_ENV, resolve_runtime_settings, validate_api_auth_settings
from nfi_engine.config import ConfigLoadError

LOCAL_API_HOST = "127.0.0.1"
CONTAINER_API_HOST: Final = "0.0.0.0"  # noqa: S104 - gated for container-local binds.
CONTAINER_BIND_ENV: Final = "NFI_ENGINE_ALLOW_CONTAINER_BIND"


def serve(
    config: Annotated[Path | None, typer.Option("--config", exists=True, dir_okay=False)] = None,
    host: Annotated[str | None, typer.Option("--host")] = None,
    port: Annotated[int | None, typer.Option("--port")] = None,
) -> None:
    try:
        settings = resolve_runtime_settings(config)
        validate_api_auth_settings(settings)
    except ConfigLoadError as exc:
        _exit_with_error(exc.code.value, exc.message)
    except ApiConfigurationError as exc:
        _exit_with_error(exc.code.value, exc.message)
    selected_host = settings.api.host if host is None else host
    selected_port = settings.api.port if port is None else port
    if not _host_is_allowed(selected_host):
        _exit_with_error("API_HOST_NOT_LOCAL", "serve only binds to 127.0.0.1 in milestone 1")
    if config is not None:
        os.environ[CONFIG_ENV] = str(config)
    uvicorn.run(
        "nfi_engine.api.app:create_app",
        factory=True,
        host=selected_host,
        port=selected_port,
    )


def _exit_with_error(code: str, message: str) -> NoReturn:
    sys.stderr.write(f"{code}: {message}\n")
    raise typer.Exit(code=1)


def _host_is_allowed(host: str) -> bool:
    if host == LOCAL_API_HOST:
        return True
    return host == CONTAINER_API_HOST and os.environ.get(CONTAINER_BIND_ENV) == "1"
