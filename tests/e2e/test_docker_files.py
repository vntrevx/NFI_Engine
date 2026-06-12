from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest
from httpx import ASGITransport, AsyncClient

from nfi_engine.api.app import create_app
from nfi_engine.config.models import ApiSettings, RuntimeSettings

if TYPE_CHECKING:
    from fastapi import FastAPI

PROJECT_ROOT: Final = Path(__file__).resolve().parents[2]


def test_dockerfile_uses_non_root_runtime_and_healthcheck() -> None:
    # Given: the container runtime recipe.
    dockerfile = _read("Dockerfile")

    # When/Then: it uses a multi-stage, labeled, non-root runtime with a healthcheck.
    assert dockerfile.count("FROM ") >= 2
    assert 'LABEL org.opencontainers.image.title="nfi-engine"' in dockerfile
    assert "useradd" in dockerfile
    assert "USER nfi" in dockerfile
    assert "HEALTHCHECK" in dockerfile


def test_dockerignore_excludes_runtime_and_secret_material() -> None:
    # Given: the build context exclusion file.
    patterns = set(_read(".dockerignore").splitlines())

    # When/Then: volatile, secret, and local runtime paths are excluded.
    for expected in (
        ".git",
        ".env",
        ".omo/evidence",
        ".venv",
        "__pycache__",
        "*.sqlite*",
        "data/",
        "logs/",
    ):
        assert expected in patterns


def test_compose_uses_local_port_healthcheck_and_named_volumes() -> None:
    # Given: the local Compose stack.
    compose = _read("compose.yaml")

    # When/Then: API, CLI, and paper services use local-safe runtime wiring.
    assert "api:" in compose
    assert "cli:" in compose
    assert "paper:" in compose
    assert '"127.0.0.1:18080:18080"' in compose
    assert "healthcheck:" in compose
    assert "nfi-data:" in compose
    assert "nfi-logs:" in compose
    assert "/config/futures-paper.yaml" in compose
    assert "./.runtime/config:/config:ro" in compose
    assert "nfi-config:" not in compose
    assert "examples/docker.env.example" in compose
    assert ".runtime/docker.env" in compose
    assert "NFI_ENGINE_API_TOKEN:" not in compose


def test_docker_env_example_has_no_real_exchange_secret_placeholders() -> None:
    # Given: the docker env example shipped to operators.
    env_example = _read("examples/docker.env.example")

    # When/Then: it configures local API auth without exchange credentials.
    assert "NFI_ENGINE_API_TOKEN=change-me-local-only" in env_example
    assert "NFI_ENGINE__EXCHANGE__API_KEY" not in env_example
    assert "NFI_ENGINE__EXCHANGE__API_SECRET" not in env_example


@pytest.mark.anyio
async def test_api_serves_local_settings_html() -> None:
    # Given: the ASGI app that Docker serves.
    settings = RuntimeSettings(
        api=ApiSettings.model_validate({"auth_token": "local-test-bearer"}),
    )
    client = _client(create_app(settings=settings))

    # When: the local frontend settings route is requested.
    login = await client.post(
        "/api/v1/session/login",
        headers={"Authorization": "Bearer local-test-bearer"},
    )
    response = await client.get("/settings")

    # Then: static HTML is returned without external asset links.
    assert login.status_code == 200
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "NFI Engine" in response.text
    assert "https://" not in response.text


def _read(relative_path: str) -> str:
    return (PROJECT_ROOT / relative_path).read_text(encoding="utf-8")


def _client(app: FastAPI) -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://testserver")
