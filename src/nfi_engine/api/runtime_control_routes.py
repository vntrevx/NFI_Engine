from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from types import MappingProxyType
from typing import TYPE_CHECKING, Final, NoReturn, assert_never

from fastapi import HTTPException, status

from nfi_engine.api.auth import ApiErrorResponse
from nfi_engine.api.errors import ApiErrorCode
from nfi_engine.api.runtime_control_models import (
    RuntimeControlCommandRequest,
    RuntimeControlResponse,
)
from nfi_engine.api.state import ApiContext
from nfi_engine.paper import BotCommand
from nfi_engine.preflight.models import PreflightReport
from nfi_engine.runtime_control import RuntimeControlCode, RuntimeControlRequest, control_runtime
from nfi_engine.runtime_health import (
    RuntimeHealthRequest,
    RuntimeHealthSnapshot,
    build_runtime_health_snapshot,
)
from nfi_engine.wallet import fetch_wallet_balance

if TYPE_CHECKING:
    from fastapi import APIRouter

_API_ERROR_CODE_MAP: Final[dict[RuntimeControlCode, ApiErrorCode]] = {
    RuntimeControlCode.RUNTIME_CONTROL_ACCEPTED: ApiErrorCode.RUNTIME_INVALID_TRANSITION,
    RuntimeControlCode.RUNTIME_ALREADY_PAUSED: ApiErrorCode.RUNTIME_ALREADY_PAUSED,
    RuntimeControlCode.RUNTIME_ALREADY_STOPPED: ApiErrorCode.RUNTIME_ALREADY_STOPPED,
    RuntimeControlCode.RUNTIME_ALREADY_RUNNING: ApiErrorCode.RUNTIME_ALREADY_RUNNING,
    RuntimeControlCode.RUNTIME_INVALID_TRANSITION: ApiErrorCode.RUNTIME_INVALID_TRANSITION,
    RuntimeControlCode.RUNTIME_PREFLIGHT_REQUIRED: ApiErrorCode.RUNTIME_PREFLIGHT_REQUIRED,
    RuntimeControlCode.RUNTIME_PREFLIGHT_BLOCKED: ApiErrorCode.RUNTIME_PREFLIGHT_BLOCKED,
    RuntimeControlCode.RUNTIME_HEALTH_REQUIRED: ApiErrorCode.RUNTIME_HEALTH_REQUIRED,
    RuntimeControlCode.RUNTIME_HEALTH_BLOCKED: ApiErrorCode.RUNTIME_HEALTH_BLOCKED,
    RuntimeControlCode.RUNTIME_LIVE_UNSAFE: ApiErrorCode.RUNTIME_LIVE_UNSAFE,
}
API_ERROR_CODES: Final[Mapping[RuntimeControlCode, ApiErrorCode]] = MappingProxyType(
    _API_ERROR_CODE_MAP,
)


def add_runtime_control_routes(
    *,
    read_router: APIRouter,
    write_router: APIRouter,
    context: ApiContext,
    readiness: PreflightReport,
) -> None:
    read_router.add_api_route(
        "/runtime/control",
        _runtime_control_status(context),
        methods=["GET"],
    )
    write_router.add_api_route(
        "/runtime/control",
        _runtime_control(context, readiness),
        methods=["POST"],
    )
    write_router.add_api_route(
        "/start",
        _runtime_command(context, readiness, BotCommand.START),
        methods=["POST"],
    )
    write_router.add_api_route(
        "/pause",
        _runtime_command(context, readiness, BotCommand.PAUSE),
        methods=["POST"],
    )
    write_router.add_api_route(
        "/resume",
        _runtime_command(context, readiness, BotCommand.RESUME),
        methods=["POST"],
    )
    write_router.add_api_route(
        "/stop",
        _runtime_command(context, readiness, BotCommand.STOP),
        methods=["POST"],
    )


def _runtime_control_status(context: ApiContext) -> Callable[[], RuntimeControlResponse]:
    def endpoint() -> RuntimeControlResponse:
        return RuntimeControlResponse.from_state(context.runtime.state)

    return endpoint


def _runtime_control(
    context: ApiContext,
    readiness: PreflightReport,
) -> Callable[[RuntimeControlCommandRequest | None], Awaitable[RuntimeControlResponse]]:
    async def endpoint(
        payload: RuntimeControlCommandRequest | None = None,
    ) -> RuntimeControlResponse:
        command = _parse_command(None if payload is None else payload.command)
        if command is None:
            _raise_command_invalid()
        return await _apply_command(context=context, readiness=readiness, command=command)

    return endpoint


def _runtime_command(
    context: ApiContext,
    readiness: PreflightReport,
    command: BotCommand,
) -> Callable[[], Awaitable[RuntimeControlResponse]]:
    async def endpoint() -> RuntimeControlResponse:
        return await _apply_command(context=context, readiness=readiness, command=command)

    return endpoint


async def _apply_command(
    *,
    context: ApiContext,
    readiness: PreflightReport,
    command: BotCommand,
) -> RuntimeControlResponse:
    health = await _health_for_command(context=context, readiness=readiness, command=command)
    result = control_runtime(
        RuntimeControlRequest(
            settings=context.settings,
            state=context.runtime.state,
            command=command,
            readiness=readiness,
            health=health,
        ),
    )
    if not result.accepted:
        _raise_control_denied(result.code, result.message)
    context.runtime.set_state(result.state)
    return RuntimeControlResponse.from_result(result)


async def _health_for_command(
    *,
    context: ApiContext,
    readiness: PreflightReport,
    command: BotCommand,
) -> RuntimeHealthSnapshot | None:
    match command:
        case BotCommand.START | BotCommand.RESUME:
            return await _runtime_health_snapshot(context=context, readiness=readiness)
        case BotCommand.PAUSE | BotCommand.STOP:
            return None
        case unreachable:
            assert_never(unreachable)


async def _runtime_health_snapshot(
    *,
    context: ApiContext,
    readiness: PreflightReport,
) -> RuntimeHealthSnapshot:
    read_models = await context.dashboard_store.read_models()
    wallet = await fetch_wallet_balance(
        settings=context.settings,
        reader=context.wallet_balance_reader,
    )
    return build_runtime_health_snapshot(
        RuntimeHealthRequest(
            settings=context.settings,
            bot_state=context.runtime.state,
            readiness=readiness,
            read_models=read_models,
            wallet_balance=wallet,
        ),
    )


def _parse_command(raw_command: str | None) -> BotCommand | None:
    if raw_command is None or raw_command == "":
        return None
    try:
        return BotCommand(raw_command)
    except ValueError:
        return None


def _raise_command_invalid() -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=ApiErrorResponse(
            code=ApiErrorCode.RUNTIME_COMMAND_INVALID,
            message="runtime command must be one of start, pause, resume, stop",
        ).model_dump(mode="json"),
    )


def _raise_control_denied(code: RuntimeControlCode, message: str) -> NoReturn:
    raise HTTPException(
        status_code=_status_for_control_code(code),
        detail=ApiErrorResponse(
            code=_api_error_code(code),
            message=message,
        ).model_dump(mode="json"),
    )


def _status_for_control_code(code: RuntimeControlCode) -> int:
    match code:
        case RuntimeControlCode.RUNTIME_CONTROL_ACCEPTED:
            return status.HTTP_200_OK
        case (
            RuntimeControlCode.RUNTIME_ALREADY_PAUSED
            | RuntimeControlCode.RUNTIME_ALREADY_STOPPED
            | RuntimeControlCode.RUNTIME_ALREADY_RUNNING
            | RuntimeControlCode.RUNTIME_INVALID_TRANSITION
            | RuntimeControlCode.RUNTIME_PREFLIGHT_REQUIRED
            | RuntimeControlCode.RUNTIME_PREFLIGHT_BLOCKED
            | RuntimeControlCode.RUNTIME_HEALTH_REQUIRED
            | RuntimeControlCode.RUNTIME_HEALTH_BLOCKED
            | RuntimeControlCode.RUNTIME_LIVE_UNSAFE
        ):
            return status.HTTP_409_CONFLICT
        case unreachable:
            assert_never(unreachable)


def _api_error_code(code: RuntimeControlCode) -> ApiErrorCode:
    return API_ERROR_CODES[code]
