from __future__ import annotations

import os
from decimal import Decimal
from pathlib import Path
from typing import Final

from nfi_engine.api.errors import ApiConfigurationError
from nfi_engine.api.settings import validate_api_auth_settings
from nfi_engine.config import ConfigLoadError, RuntimeSettings, load_runtime_settings
from nfi_engine.domain import TradingMode
from nfi_engine.preflight.models import (
    PreflightCheck,
    PreflightCode,
    PreflightReport,
    PreflightStatus,
)
from nfi_engine.preflight.reconciliation import reconciliation_check
from nfi_engine.profiles import ProfileError, get_operator_profile

SQLITE_PREFIX: Final = "sqlite+aiosqlite:///"
LOCAL_API_HOST: Final = "127.0.0.1"
FUTURES_LEVERAGE_CEILING: Final = Decimal(10)
REQUIRED_COMPOSE_VOLUMES: Final = ("nfi-data", "nfi-logs", "nfi-config")


def run_preflight_for_config(*, config_path: Path, profile_name: str) -> PreflightReport:
    try:
        settings = load_runtime_settings(config_path)
    except ConfigLoadError as exc:
        return _report(
            profile_name,
            (
                _check(
                    PreflightCode.CONFIG_INVALID,
                    PreflightStatus.BLOCK,
                    f"{exc.code.value}: {exc.message}",
                ),
            ),
        )
    return run_preflight(settings=settings, profile_name=profile_name, config_path=config_path)


def run_preflight(
    *,
    settings: RuntimeSettings,
    profile_name: str,
    config_path: Path | None = None,
) -> PreflightReport:
    checks: list[PreflightCheck] = [_config_valid_check(config_path)]
    checks.append(_profile_check(settings=settings, profile_name=profile_name))
    checks.append(_api_bind_check(settings))
    checks.append(_api_token_check(settings))
    checks.append(_live_scope_check(settings))
    checks.append(_futures_leverage_check(settings))
    checks.append(_exchange_mode_check(settings))
    checks.append(_database_path_check(settings))
    checks.append(_log_path_check(settings))
    checks.append(_docker_volume_check())
    checks.append(_notifier_check(settings))
    checks.append(_pair_config_check(settings))
    checks.append(reconciliation_check(settings))
    return _report(profile_name, tuple(checks))


def _config_valid_check(config_path: Path | None) -> PreflightCheck:
    location = "runtime settings" if config_path is None else str(config_path)
    return _check(PreflightCode.CONFIG_VALID, PreflightStatus.PASS, f"loaded {location}")


def _profile_check(*, settings: RuntimeSettings, profile_name: str) -> PreflightCheck:
    try:
        profile = get_operator_profile(profile_name)
    except ProfileError as exc:
        return _check(PreflightCode.PROFILE_CONFIG_MISMATCH, PreflightStatus.BLOCK, str(exc))
    if settings.exchange.trading_mode not in profile.trading_modes:
        return _check(
            PreflightCode.PROFILE_CONFIG_MISMATCH,
            PreflightStatus.BLOCK,
            f"{profile.name} does not allow {settings.exchange.trading_mode.value}",
        )
    if profile.name == "bybit-testnet" and settings.exchange.name != "bybit":
        return _check(
            PreflightCode.PROFILE_CONFIG_MISMATCH,
            PreflightStatus.BLOCK,
            "bybit-testnet requires exchange.name=bybit",
        )
    if profile.read_only and not settings.ui.read_only:
        return _check(
            PreflightCode.PROFILE_CONFIG_MISMATCH,
            PreflightStatus.BLOCK,
            f"{profile.name} requires ui.read_only=true",
        )
    return _check(PreflightCode.PROFILE_COMPATIBLE, PreflightStatus.PASS, profile.description)


def _api_bind_check(settings: RuntimeSettings) -> PreflightCheck:
    if settings.api.host != LOCAL_API_HOST:
        return _check(
            PreflightCode.PUBLIC_BIND_NOT_ALLOWED,
            PreflightStatus.BLOCK,
            "api.host must stay bound to 127.0.0.1 in milestone 1",
        )
    return _check(PreflightCode.PUBLIC_BIND_NOT_ALLOWED, PreflightStatus.PASS, "api bind is local")


def _api_token_check(settings: RuntimeSettings) -> PreflightCheck:
    try:
        validate_api_auth_settings(settings)
    except ApiConfigurationError as exc:
        return _check(PreflightCode.WEAK_API_TOKEN, PreflightStatus.BLOCK, str(exc))
    return _check(PreflightCode.WEAK_API_TOKEN, PreflightStatus.PASS, "api auth policy passed")


def _live_scope_check(settings: RuntimeSettings) -> PreflightCheck:
    if settings.engine.live_trading:
        return _check(
            PreflightCode.LIVE_TRADING_OUT_OF_SCOPE,
            PreflightStatus.BLOCK,
            "milestone 1 does not allow live real-money orders",
        )
    return _check(
        PreflightCode.LIVE_TRADING_DISABLED,
        PreflightStatus.PASS,
        "live trading is disabled",
    )


def _futures_leverage_check(settings: RuntimeSettings) -> PreflightCheck:
    if settings.exchange.trading_mode is not TradingMode.FUTURES:
        return _check(PreflightCode.FUTURES_LEVERAGE_INVALID, PreflightStatus.PASS, "spot mode")
    if (
        settings.risk.leverage > settings.risk.max_leverage
        or settings.risk.leverage > FUTURES_LEVERAGE_CEILING
    ):
        return _check(
            PreflightCode.FUTURES_LEVERAGE_INVALID,
            PreflightStatus.BLOCK,
            "futures leverage exceeds readiness ceiling",
        )
    return _check(
        PreflightCode.FUTURES_LEVERAGE_INVALID,
        PreflightStatus.PASS,
        "futures leverage guardrails passed",
    )


def _exchange_mode_check(settings: RuntimeSettings) -> PreflightCheck:
    if settings.exchange.name == "bybit" and not settings.exchange.testnet:
        return _check(
            PreflightCode.EXCHANGE_TESTNET_REQUIRED,
            PreflightStatus.BLOCK,
            "Bybit adapter must use testnet=true in milestone 1",
        )
    return _check(
        PreflightCode.EXCHANGE_TESTNET_REQUIRED,
        PreflightStatus.PASS,
        "exchange mode is simulator or testnet",
    )


def _database_path_check(settings: RuntimeSettings) -> PreflightCheck:
    path = _sqlite_path(settings.database.url)
    if path is None or _path_parent_is_creatable(path):
        return _check(PreflightCode.DB_PATH_READY, PreflightStatus.PASS, "SQLite path is ready")
    return _check(
        PreflightCode.DB_PATH_MISSING,
        PreflightStatus.BLOCK,
        f"SQLite parent is not writable: {path.parent}",
    )


def _log_path_check(settings: RuntimeSettings) -> PreflightCheck:
    path = Path(settings.notifications.jsonl_path)
    if not settings.notifications.enabled or _path_parent_is_creatable(path):
        return _check(PreflightCode.LOG_PATH_READY, PreflightStatus.PASS, "log path is writable")
    return _check(
        PreflightCode.LOG_PATH_NOT_WRITABLE,
        PreflightStatus.BLOCK,
        f"log parent is not writable: {path.parent}",
    )


def _docker_volume_check() -> PreflightCheck:
    compose = Path("compose.yaml")
    if not compose.exists():
        return _check(
            PreflightCode.DOCKER_VOLUMES_MISSING,
            PreflightStatus.BLOCK,
            "compose.yaml is missing",
        )
    content = compose.read_text(encoding="utf-8")
    if all(volume in content for volume in REQUIRED_COMPOSE_VOLUMES):
        return _check(
            PreflightCode.DOCKER_VOLUMES_READY,
            PreflightStatus.PASS,
            "compose named volumes are configured",
        )
    return _check(
        PreflightCode.DOCKER_VOLUMES_MISSING,
        PreflightStatus.BLOCK,
        "compose named volumes are incomplete",
    )


def _notifier_check(settings: RuntimeSettings) -> PreflightCheck:
    if not settings.notifications.enabled:
        return _check(
            PreflightCode.NOTIFIER_DISABLED,
            PreflightStatus.WARN,
            "notifications are disabled",
        )
    return _check(
        PreflightCode.NOTIFIER_DRY_RUN_READY,
        PreflightStatus.PASS,
        "notifier dry-run path is configured",
    )


def _pair_config_check(settings: RuntimeSettings) -> PreflightCheck:
    locked_pairs = tuple(pair for pair in settings.risk.locked_pairs.split(",") if pair != "")
    invalid = tuple(pair for pair in locked_pairs if "/" not in pair)
    if invalid:
        return _check(
            PreflightCode.PAIR_CONFIG_VALID,
            PreflightStatus.BLOCK,
            f"invalid locked pair values: {','.join(invalid)}",
        )
    return _check(PreflightCode.PAIR_CONFIG_VALID, PreflightStatus.PASS, "pair config passed")


def _sqlite_path(database_url: str) -> Path | None:
    if not database_url.startswith(SQLITE_PREFIX):
        return None
    path_text = database_url.removeprefix(SQLITE_PREFIX)
    if path_text in {"", ":memory:"}:
        return None
    return Path(path_text)


def _path_parent_is_creatable(path: Path) -> bool:
    parent = path.parent
    if parent.exists():
        return parent.is_dir() and os.access(parent, os.W_OK)
    nearest = parent
    while not nearest.exists() and nearest != nearest.parent:
        nearest = nearest.parent
    return nearest.exists() and os.access(nearest, os.W_OK)


def _check(
    code: PreflightCode,
    status: PreflightStatus,
    message: str,
) -> PreflightCheck:
    return PreflightCheck(code=code, status=status, message=message)


def _report(profile_name: str, checks: tuple[PreflightCheck, ...]) -> PreflightReport:
    blocked = any(check.status is PreflightStatus.BLOCK for check in checks)
    return PreflightReport(profile=profile_name, blocked=blocked, checks=checks)
