from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from nfi_engine.api.errors import ApiConfigurationError, ApiErrorCode
from nfi_engine.config import RuntimeSettings, load_runtime_settings

CONFIG_ENV: Final = "NFI_ENGINE_CONFIG"
BEARER_ENV: Final = "NFI_ENGINE_API_TOKEN"
OPERATOR_USERNAME_ENV: Final = "NFI_ENGINE_OPERATOR_USERNAME"
OPERATOR_PASSWORD_ENV: Final = "NFI_ENGINE_OPERATOR_PASSWORD"  # noqa: S105
LOCAL_ENVIRONMENTS: Final = frozenset(("local", "dev", "development", "test"))
WEAK_TOKENS: Final = frozenset(("changeme", "change-me", "secret", "test-token", "password"))
MIN_PRODUCTION_TOKEN_LENGTH: Final = 16


def resolve_runtime_settings(config_path: Path | None = None) -> RuntimeSettings:
    selected_path = resolve_runtime_config_path(config_path)
    settings = (
        load_runtime_settings(selected_path) if selected_path is not None else RuntimeSettings()
    )
    bearer = os.environ.get(BEARER_ENV)
    operator_username = os.environ.get(OPERATOR_USERNAME_ENV)
    operator_password = os.environ.get(OPERATOR_PASSWORD_ENV)
    password = operator_password
    if password is None and bearer is not None and settings.api.operator_password is None:
        password = bearer
    if bearer is None and operator_username is None and password is None:
        return settings
    api_settings = settings.api.model_copy(
        update={
            "auth_token": bearer or settings.api.auth_token,
            "operator_username": operator_username or settings.api.operator_username,
            "operator_password": password or settings.api.operator_password,
        },
    )
    return settings.model_copy(update={"api": api_settings})


def validate_api_auth_settings(settings: RuntimeSettings) -> None:
    if settings.engine.environment in LOCAL_ENVIRONMENTS:
        return
    token = settings.api.auth_token
    password = settings.api.operator_password
    has_strong_token = token is not None and len(token) >= MIN_PRODUCTION_TOKEN_LENGTH
    has_strong_password = password is not None and len(password) >= MIN_PRODUCTION_TOKEN_LENGTH
    if (not has_strong_token and not has_strong_password) or token in WEAK_TOKENS:
        raise ApiConfigurationError(
            code=ApiErrorCode.API_WEAK_AUTH_VALUE,
            message="non-local API environments require strong operator credentials",
        )


def resolve_runtime_config_path(config_path: Path | None = None) -> Path | None:
    return config_path or _env_config_path()


def _env_config_path() -> Path | None:
    raw_path = os.environ.get(CONFIG_ENV)
    if raw_path is None or raw_path == "":
        return None
    return Path(raw_path)
