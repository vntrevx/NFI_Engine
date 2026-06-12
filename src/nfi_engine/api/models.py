from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from nfi_engine import __version__
from nfi_engine.config import FieldMetadata, LogLevel, RuntimeSettings, frontend_metadata
from nfi_engine.events import REDACTED_TEXT, EventCode
from nfi_engine.observability import new_correlation_id
from nfi_engine.paper import BotState

REDACTED = REDACTED_TEXT


class StrictApiModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)


class PingResponse(StrictApiModel):
    status: str


class HealthResponse(StrictApiModel):
    status: str
    host: str
    version: str


class StateResponse(StrictApiModel):
    state: BotState


class StatusResponse(StrictApiModel):
    state: BotState
    trading_mode: str
    exchange: str
    live_orders: bool
    open_trades: int
    pair_count: int


class ProfitResponse(StrictApiModel):
    total_profit: Decimal
    closed_trades: int


class TradeListResponse(StrictApiModel):
    items: tuple[str, ...]


class LockListResponse(StrictApiModel):
    items: tuple[str, ...]


class StrategyItemResponse(StrictApiModel):
    name: str
    module: str
    timeframe: str
    can_short: bool


class StrategyListResponse(StrictApiModel):
    items: tuple[StrategyItemResponse, ...]


class PairHistoryResponse(StrictApiModel):
    pair: str
    candles: tuple[str, ...]


class ConfigFieldResponse(StrictApiModel):
    path: str
    frontend_editable: bool
    sensitive: bool
    restart_required: bool
    runtime_apply_safe: bool


class ConfigSchemaResponse(StrictApiModel):
    fields: tuple[ConfigFieldResponse, ...]


class EngineConfigResponse(StrictApiModel):
    live_trading: bool
    live_trading_confirmed: bool
    environment: str


class ExchangeConfigResponse(StrictApiModel):
    name: str
    trading_mode: str
    margin_mode: str | None
    testnet: bool
    api_key: str
    api_secret: str


class ApiConfigResponse(StrictApiModel):
    host: str
    port: int
    auth_token: str
    csrf_enabled: bool


class RiskConfigResponse(StrictApiModel):
    stake_usdt: Decimal
    max_open_trades: int


class UiConfigResponse(StrictApiModel):
    locale: str
    read_only: bool


class ConfigCurrentResponse(StrictApiModel):
    engine: EngineConfigResponse
    exchange: ExchangeConfigResponse
    risk: RiskConfigResponse
    ui: UiConfigResponse
    api: ApiConfigResponse


class ConfigFieldPatch(StrictApiModel):
    path: str
    value: str


class ConfigMutationRequest(StrictApiModel):
    fields: tuple[ConfigFieldPatch, ...] = ()


class ConfigDraftResponse(StrictApiModel):
    draft_id: str
    accepted: bool


class ConfigValidationResponse(StrictApiModel):
    valid: bool
    errors: tuple[str, ...]


class ConfigApplyResponse(StrictApiModel):
    applied: bool
    restart_required: bool
    errors: tuple[str, ...] = ()
    next_action: str | None = None


class SetupPreviewResponse(StrictApiModel):
    valid: bool
    errors: tuple[str, ...]
    redacted_config: ConfigCurrentResponse | None
    config_preview: str


class LogEntryResponse(StrictApiModel):
    at: datetime
    level: LogLevel
    code: str
    message: str
    correlation_id: str
    command: str | None
    route: str | None
    safe_summary: str
    report_hint: str


class LogListResponse(StrictApiModel):
    items: tuple[LogEntryResponse, ...]


class ErrorLookupResponse(StrictApiModel):
    code: str
    message: str
    reportable: bool
    correlation_id: str
    safe_summary: str
    report_hint: str


class SupportBundleResponse(StrictApiModel):
    generated_at: datetime
    engine_version: str
    redacted_config: ConfigCurrentResponse
    logs: tuple[LogEntryResponse, ...]


class SecuritySessionResponse(StrictApiModel):
    role: str
    csrf_token: str
    expires_at: datetime


class SessionLogoutResponse(StrictApiModel):
    logged_out: bool


class SecurityAuditEventResponse(StrictApiModel):
    code: str
    route: str
    role: str


class SecurityAuditLogResponse(StrictApiModel):
    items: tuple[SecurityAuditEventResponse, ...]


class BackupRestoreResponse(StrictApiModel):
    restored: bool
    audit_event: str


def config_current_response(settings: RuntimeSettings) -> ConfigCurrentResponse:
    return ConfigCurrentResponse(
        engine=EngineConfigResponse(
            live_trading=settings.engine.live_trading,
            live_trading_confirmed=settings.engine.live_trading_confirmed,
            environment=settings.engine.environment,
        ),
        exchange=ExchangeConfigResponse(
            name=settings.exchange.name,
            trading_mode=settings.exchange.trading_mode.value,
            margin_mode=(
                None
                if settings.exchange.margin_mode is None
                else settings.exchange.margin_mode.value
            ),
            testnet=settings.exchange.testnet,
            api_key=REDACTED,
            api_secret=REDACTED,
        ),
        risk=RiskConfigResponse(
            stake_usdt=settings.risk.stake_usdt,
            max_open_trades=settings.risk.max_open_trades,
        ),
        ui=UiConfigResponse(
            locale=settings.ui.locale.value,
            read_only=settings.ui.read_only,
        ),
        api=ApiConfigResponse(
            host=settings.api.host,
            port=settings.api.port,
            auth_token=REDACTED,
            csrf_enabled=settings.api.csrf_enabled,
        ),
    )


def config_schema_response() -> ConfigSchemaResponse:
    return ConfigSchemaResponse(fields=tuple(_field_response(item) for item in frontend_metadata()))


def strategy_item_response(settings: RuntimeSettings) -> StrategyItemResponse:
    return StrategyItemResponse(
        name=settings.strategy.name,
        module=settings.strategy.module,
        timeframe="5m",
        can_short=settings.exchange.trading_mode.value == "futures",
    )


def initial_log_entries() -> tuple[LogEntryResponse, ...]:
    return (
        LogEntryResponse(
            at=datetime.now(UTC),
            level=LogLevel.INFO,
            code="API_STARTED",
            message="api app initialized",
            correlation_id=new_correlation_id(),
            command=None,
            route="/api/v1",
            safe_summary="api app initialized",
            report_hint="include recent logs and support bundle",
        ),
        LogEntryResponse(
            at=datetime.now(UTC),
            level=LogLevel.ERROR,
            code=EventCode.CONFIG_VALIDATION_ERROR.value,
            message="config validation failed",
            correlation_id=new_correlation_id(),
            command="config validate",
            route="/api/v1/config/validate",
            safe_summary="config validation failed",
            report_hint="attach redacted config, command output, and recent logs",
        ),
    )


def support_bundle_response(
    *,
    settings: RuntimeSettings,
    logs: tuple[LogEntryResponse, ...],
) -> SupportBundleResponse:
    return SupportBundleResponse(
        generated_at=datetime.now(UTC),
        engine_version=__version__,
        redacted_config=config_current_response(settings),
        logs=logs,
    )


def _field_response(item: FieldMetadata) -> ConfigFieldResponse:
    return ConfigFieldResponse(
        path=item.path,
        frontend_editable=item.frontend_editable,
        sensitive=item.sensitive,
        restart_required=item.restart_required,
        runtime_apply_safe=item.runtime_apply_safe,
    )
