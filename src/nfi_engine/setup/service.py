from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import NoReturn

from nfi_engine.config import ConfigLoadError, validate_runtime_settings
from nfi_engine.config.models import EngineSettings, ExchangeSettings, RiskSettings, RuntimeSettings
from nfi_engine.domain import MarginMode, TradingMode
from nfi_engine.events import REDACTED_TEXT
from nfi_engine.events.redaction import redact_text
from nfi_engine.setup.models import RiskPreset, SetupIntent, SetupPlan, SetupRequest

PREVIEW_PATH = Path("<setup-preview>")


@dataclass(frozen=True, slots=True)
class SetupError(Exception):
    code: str
    message: str


def build_setup_plan(request: SetupRequest) -> SetupPlan:
    try:
        settings = _settings_from_request(request)
        config_text = render_setup_config(settings)
    except ValueError as exc:
        return _invalid_plan(error=str(exc), request=request)
    redacted = _redact_config(config_text=config_text, request=request)
    try:
        validate_runtime_settings(settings=settings, path=PREVIEW_PATH)
    except ConfigLoadError as exc:
        return SetupPlan(
            valid=False,
            errors=(exc.code.value,),
            settings=None,
            config_text=config_text,
            redacted_config_text=redacted,
        )
    return SetupPlan(
        valid=True,
        errors=(),
        settings=settings,
        config_text=config_text,
        redacted_config_text=redacted,
    )


def write_setup_config(*, request: SetupRequest, config_path: Path, overwrite: bool) -> SetupPlan:
    if config_path.exists() and not overwrite:
        raise SetupError(code="SETUP_CONFIG_EXISTS", message="config already exists")
    plan = build_setup_plan(request)
    if not plan.valid:
        _raise_setup_validation(plan)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(plan.config_text, encoding="utf-8")
    return SetupPlan(
        valid=plan.valid,
        errors=plan.errors,
        settings=plan.settings,
        config_text=plan.config_text,
        redacted_config_text=plan.redacted_config_text,
        config_path=config_path,
    )


def render_setup_config(settings: RuntimeSettings) -> str:
    lines = [
        "engine:",
        f"  live_trading: {_bool(settings.engine.live_trading)}",
        f"  live_trading_confirmed: {_bool(settings.engine.live_trading_confirmed)}",
        f"  environment: {_yaml_scalar(settings.engine.environment)}",
        "exchange:",
        f"  name: {_yaml_scalar(settings.exchange.name)}",
        f"  trading_mode: {_yaml_scalar(settings.exchange.trading_mode.value)}",
    ]
    if settings.exchange.margin_mode is not None:
        lines.append(f"  margin_mode: {_yaml_scalar(settings.exchange.margin_mode.value)}")
    lines.extend(
        (
            f"  testnet: {_bool(settings.exchange.testnet)}",
            f"  api_key: {_nullable(settings.exchange.api_key)}",
            f"  api_secret: {_nullable(settings.exchange.api_secret)}",
            "risk:",
            f"  stake_usdt: {_yaml_scalar(str(settings.risk.stake_usdt))}",
            f"  leverage: {_yaml_scalar(str(settings.risk.leverage))}",
            f"  max_leverage: {_yaml_scalar(str(settings.risk.max_leverage))}",
            f"  max_open_trades: {settings.risk.max_open_trades}",
            "ui:",
            f"  locale: {_yaml_scalar(settings.ui.locale.value)}",
            "api:",
            f"  host: {_yaml_scalar(settings.api.host)}",
            f"  port: {settings.api.port}",
            "  csrf_enabled: true",
        )
    )
    return "\n".join(lines) + "\n"


def _settings_from_request(request: SetupRequest) -> RuntimeSettings:
    return RuntimeSettings(
        engine=EngineSettings(
            live_trading=request.intent is SetupIntent.LIVE,
            live_trading_confirmed=request.live_trading_confirmed,
        ),
        exchange=ExchangeSettings(
            name=request.exchange,
            trading_mode=request.trading_mode,
            margin_mode=_margin_mode(request),
            testnet=request.intent is not SetupIntent.LIVE,
            api_key=request.api_key or None,
            api_secret=request.api_secret or None,
        ),
        risk=_risk_settings(request),
        ui=RuntimeSettings().ui.model_copy(update={"locale": request.locale}),
    )


def _margin_mode(request: SetupRequest) -> MarginMode | None:
    if request.trading_mode is TradingMode.SPOT:
        return request.margin_mode
    return request.margin_mode or MarginMode.ISOLATED


def _risk_settings(request: SetupRequest) -> RiskSettings:
    profile = _risk_profile(request.risk_preset)
    leverage = profile.leverage if request.trading_mode is TradingMode.FUTURES else Decimal(1)
    return RiskSettings(
        stake_usdt=profile.stake_usdt,
        leverage=leverage,
        max_leverage=Decimal(5),
        max_open_trades=profile.max_open_trades,
    )


@dataclass(frozen=True, slots=True)
class _RiskProfile:
    stake_usdt: Decimal
    leverage: Decimal
    max_open_trades: int


def _risk_profile(preset: RiskPreset) -> _RiskProfile:
    match preset:
        case RiskPreset.CONSERVATIVE:
            return _RiskProfile(stake_usdt=Decimal(10), leverage=Decimal(1), max_open_trades=2)
        case RiskPreset.BALANCED:
            return _RiskProfile(stake_usdt=Decimal(25), leverage=Decimal(2), max_open_trades=3)
        case RiskPreset.AGGRESSIVE:
            return _RiskProfile(stake_usdt=Decimal(50), leverage=Decimal(3), max_open_trades=5)


def _invalid_plan(*, error: str, request: SetupRequest) -> SetupPlan:
    return SetupPlan(
        valid=False,
        errors=(error,),
        settings=None,
        config_text="",
        redacted_config_text=REDACTED_TEXT if _secrets(request) else "",
    )


def _raise_setup_validation(plan: SetupPlan) -> NoReturn:
    message = ", ".join(plan.errors)
    raise SetupError(code=plan.errors[0], message=message)


def _redact_config(*, config_text: str, request: SetupRequest) -> str:
    return redact_text(config_text, secrets=_secrets(request))


def _secrets(request: SetupRequest) -> tuple[str, ...]:
    return tuple(secret for secret in (request.api_key, request.api_secret) if secret)


def _nullable(value: str | None) -> str:
    if value is None:
        return "null"
    return _yaml_scalar(value)


def _yaml_scalar(value: str) -> str:
    if "\n" in value or "\r" in value:
        message = "setup YAML values must be single-line"
        raise ValueError(message)
    if "'" not in value:
        return f"'{value}'"
    if '"' not in value:
        return f'"{value}"'
    message = "setup YAML values cannot contain both quote characters"
    raise ValueError(message)


def _bool(value: bool) -> str:
    return str(value).lower()
