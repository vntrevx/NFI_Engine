from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response, WebSocket, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from nfi_engine.api.auth import OperatorIdentity
from nfi_engine.api.config_routes import add_config_routes
from nfi_engine.api.dashboard_routes import add_dashboard_routes
from nfi_engine.api.log_lookup import error_lookup_response
from nfi_engine.api.models import (
    BackupRestoreResponse,
    ErrorLookupResponse,
    HealthResponse,
    LockListResponse,
    LogEntryResponse,
    LogListResponse,
    PairHistoryResponse,
    PingResponse,
    ProfitResponse,
    StateResponse,
    StatusResponse,
    StrategyItemResponse,
    StrategyListResponse,
    SupportBundleResponse,
    TradeListResponse,
    strategy_item_response,
    support_bundle_response,
)
from nfi_engine.api.pairlist_routes import add_pairlist_routes
from nfi_engine.api.security import SecurityContext
from nfi_engine.api.security_routes import add_security_audit_route, add_security_routes
from nfi_engine.api.setup_routes import add_setup_routes
from nfi_engine.api.state import ApiContext
from nfi_engine.api.support_bundle import support_bundle_zip
from nfi_engine.config import LogLevel
from nfi_engine.dashboard import summarize_dashboard_read_models
from nfi_engine.paper import BotCommand
from nfi_engine.preflight.models import PreflightReport

bearer_scheme = HTTPBearer(auto_error=False)


def build_api_router(
    context: ApiContext,
    *,
    logs: tuple[LogEntryResponse, ...],
    security: SecurityContext,
    readiness: PreflightReport,
) -> APIRouter:
    def require_operator(
        request: Request,
        credentials: Annotated[
            HTTPAuthorizationCredentials | None,
            Depends(bearer_scheme),
        ],
    ) -> OperatorIdentity:
        return security.require_operator(request, credentials)

    def require_csrf(request: Request) -> None:
        security.require_csrf(request)

    def require_write(request: Request) -> None:
        security.require_write(request)

    public_router = APIRouter()
    protected_router = APIRouter(dependencies=[Depends(require_operator)])
    write_router = APIRouter(
        dependencies=[
            Depends(require_operator),
            Depends(require_csrf),
            Depends(require_write),
        ],
    )

    public_router.add_api_route("/ping", _ping, methods=["GET"])
    public_router.add_api_route("/health", _health(context), methods=["GET"])
    add_security_routes(public_router, security)
    add_security_audit_route(protected_router, security)
    write_router.add_api_route(
        "/start",
        _state_command(context, BotCommand.START),
        methods=["POST"],
    )
    write_router.add_api_route(
        "/pause",
        _state_command(context, BotCommand.PAUSE),
        methods=["POST"],
    )
    write_router.add_api_route(
        "/stop",
        _state_command(context, BotCommand.STOP),
        methods=["POST"],
    )
    protected_router.add_api_route("/status", _status(context), methods=["GET"])
    protected_router.add_api_route("/profit", _profit(context), methods=["GET"])
    protected_router.add_api_route("/trades", _trades(context), methods=["GET"])
    protected_router.add_api_route("/locks", _locks, methods=["GET"])
    add_dashboard_routes(protected_router, context=context, logs=logs, readiness=readiness)
    protected_router.add_api_route("/strategies", _strategies(context), methods=["GET"])
    protected_router.add_api_route("/strategy/{name}", _strategy_detail(context), methods=["GET"])
    protected_router.add_api_route("/pair_history", _pair_history, methods=["GET"])
    add_setup_routes(protected_router)
    add_pairlist_routes(read_router=protected_router, write_router=write_router, context=context)
    add_config_routes(read_router=protected_router, write_router=write_router, context=context)
    write_router.add_api_route("/backup/restore", _backup_restore, methods=["POST"])
    protected_router.add_api_route("/logs/recent", _logs_recent(logs), methods=["GET"])
    protected_router.add_api_route("/logs/search", _logs_search(logs), methods=["GET"])
    protected_router.add_api_route("/errors/{code}", _error_lookup(logs), methods=["GET"])
    protected_router.add_api_route(
        "/reports/support-bundle",
        _support_bundle(context, logs),
        methods=["GET"],
    )
    protected_router.add_api_route(
        "/reports/support-bundle.zip",
        _support_bundle_zip(context, logs),
        methods=["GET"],
    )
    public_router.add_api_websocket_route("/message/ws", _message_ws(security))

    public_router.include_router(protected_router)
    public_router.include_router(write_router)
    return public_router


def _ping() -> PingResponse:
    return PingResponse(status="pong")


def _health(context: ApiContext) -> Callable[[], HealthResponse]:
    def endpoint() -> HealthResponse:
        return HealthResponse(status="ok", host=context.settings.api.host, version="0.1.0")

    return endpoint


def _state_command(context: ApiContext, command: BotCommand) -> Callable[[], StateResponse]:
    def endpoint() -> StateResponse:
        return StateResponse(state=context.runtime.apply(command))

    return endpoint


def _status(context: ApiContext) -> Callable[[], Awaitable[StatusResponse]]:
    async def endpoint() -> StatusResponse:
        read_models = await context.dashboard_store.read_models()
        summary = summarize_dashboard_read_models(read_models)
        return StatusResponse(
            state=context.runtime.state,
            trading_mode=context.settings.exchange.trading_mode.value,
            exchange=context.settings.exchange.name,
            live_orders=False,
            open_trades=summary.open_trades,
            pair_count=_pair_count(context),
        )

    return endpoint


def _profit(context: ApiContext) -> Callable[[], Awaitable[ProfitResponse]]:
    async def endpoint() -> ProfitResponse:
        read_models = await context.dashboard_store.read_models()
        summary = summarize_dashboard_read_models(read_models)
        return ProfitResponse(
            total_profit=summary.session_profit,
            closed_trades=summary.closed_trades,
        )

    return endpoint


def _trades(context: ApiContext) -> Callable[[], Awaitable[TradeListResponse]]:
    async def endpoint() -> TradeListResponse:
        read_models = await context.dashboard_store.read_models()
        summary = summarize_dashboard_read_models(read_models)
        return TradeListResponse(items=summary.trade_ids)

    return endpoint


def _locks() -> LockListResponse:
    return LockListResponse(items=())


def _pair_count(context: ApiContext) -> int:
    return len(
        tuple(
            pair.strip() for pair in context.settings.pairlist.whitelist.split(",") if pair.strip()
        ),
    )


def _strategies(context: ApiContext) -> Callable[[], StrategyListResponse]:
    def endpoint() -> StrategyListResponse:
        return StrategyListResponse(items=(strategy_item_response(context.settings),))

    return endpoint


def _strategy_detail(context: ApiContext) -> Callable[[str], StrategyItemResponse]:
    def endpoint(name: str) -> StrategyItemResponse:
        current = strategy_item_response(context.settings)
        if name != current.name:
            return StrategyItemResponse(name=name, module="", timeframe="", can_short=False)
        return current

    return endpoint


def _pair_history(pair: Annotated[str, Query(min_length=3)]) -> PairHistoryResponse:
    return PairHistoryResponse(pair=pair, candles=())


def _backup_restore() -> BackupRestoreResponse:
    return BackupRestoreResponse(restored=False, audit_event="BACKUP_RESTORE_PREVIEW_REQUIRED")


def _logs_recent(
    logs: tuple[LogEntryResponse, ...],
) -> Callable[[int, LogLevel | None], LogListResponse]:
    def endpoint(
        limit: Annotated[int, Query(ge=1, le=200)] = 50,
        severity: LogLevel | None = None,
    ) -> LogListResponse:
        selected = (
            logs if severity is None else tuple(item for item in logs if item.level is severity)
        )
        return LogListResponse(items=selected[:limit])

    return endpoint


def _logs_search(logs: tuple[LogEntryResponse, ...]) -> Callable[[str], LogListResponse]:
    def endpoint(q: Annotated[str, Query(min_length=1)] = "api") -> LogListResponse:
        normalized_query = q.lower()
        return LogListResponse(
            items=tuple(
                item
                for item in logs
                if normalized_query in item.message.lower()
                or normalized_query in item.code.lower()
                or normalized_query in item.safe_summary.lower()
            ),
        )

    return endpoint


def _error_lookup(logs: tuple[LogEntryResponse, ...]) -> Callable[[str], ErrorLookupResponse]:
    def endpoint(code: str) -> ErrorLookupResponse:
        return error_lookup_response(logs=logs, code=code)

    return endpoint


def _support_bundle(
    context: ApiContext,
    logs: tuple[LogEntryResponse, ...],
) -> Callable[[], SupportBundleResponse]:
    def endpoint() -> SupportBundleResponse:
        return support_bundle_response(settings=context.settings, logs=logs)

    return endpoint


def _support_bundle_zip(
    context: ApiContext,
    logs: tuple[LogEntryResponse, ...],
) -> Callable[[], Response]:
    def endpoint() -> Response:
        payload = support_bundle_response(settings=context.settings, logs=logs)
        return Response(
            content=support_bundle_zip(payload),
            media_type="application/zip",
            headers={"content-disposition": "attachment; filename=nfi-support-report.zip"},
        )

    return endpoint


def _message_ws(security: SecurityContext) -> Callable[[WebSocket], Awaitable[None]]:
    async def endpoint(websocket: WebSocket) -> None:
        if not security.accepts_session_id(websocket.cookies.get("nfi_engine_session")):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        await websocket.accept()
        await websocket.send_json({"status": "connected"})
        await websocket.close()

    return endpoint
