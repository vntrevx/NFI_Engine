from __future__ import annotations

from typing import assert_never

from nfi_engine.paper import BotCommand, BotState
from nfi_engine.runtime_control.models import (
    RuntimeControlCode,
    RuntimeControlRequest,
    RuntimeControlResult,
)
from nfi_engine.runtime_health import RuntimeHealthState

LIVE_ORDER_NOOP = "No live exchange order cancellation is performed by this control."


def control_runtime(request: RuntimeControlRequest) -> RuntimeControlResult:
    match request.command:
        case BotCommand.START:
            return _start(request)
        case BotCommand.PAUSE:
            return _pause(request)
        case BotCommand.RESUME:
            return _resume(request)
        case BotCommand.STOP:
            return _stop(request)
        case unreachable:
            assert_never(unreachable)


def new_entries_allowed(state: BotState) -> bool:
    match state:
        case BotState.RUNNING:
            return True
        case BotState.STOPPED | BotState.PAUSED | BotState.STOPPING:
            return False
        case unreachable:
            assert_never(unreachable)


def _start(request: RuntimeControlRequest) -> RuntimeControlResult:
    match request.state:
        case BotState.STOPPED:
            gate = _resume_gate(request)
            if gate is not None:
                return gate
            return _accepted(
                request,
                state=BotState.RUNNING,
                message="runtime started after safety gates passed",
                next_action="Monitor runtime health before increasing risk.",
            )
        case BotState.RUNNING:
            return _denied(
                request,
                code=RuntimeControlCode.RUNTIME_ALREADY_RUNNING,
                message="runtime is already running",
                next_action="Use pause or stop if the run should change state.",
            )
        case BotState.PAUSED:
            return _denied(
                request,
                code=RuntimeControlCode.RUNTIME_INVALID_TRANSITION,
                message="paused runtime must be resumed, not started",
                next_action="Use resume after preflight and runtime health are clear.",
            )
        case BotState.STOPPING:
            return _denied(
                request,
                code=RuntimeControlCode.RUNTIME_INVALID_TRANSITION,
                message="runtime is stopping",
                next_action="Wait for stop to settle before starting again.",
            )
        case unreachable:
            assert_never(unreachable)


def _pause(request: RuntimeControlRequest) -> RuntimeControlResult:
    match request.state:
        case BotState.RUNNING:
            return _accepted(
                request,
                state=BotState.PAUSED,
                message="new entries are paused; existing state remains inspectable",
                next_action="Inspect runtime health before resuming entries.",
            )
        case BotState.PAUSED:
            return _denied(
                request,
                code=RuntimeControlCode.RUNTIME_ALREADY_PAUSED,
                message="runtime is already paused",
                next_action="Use resume or stop.",
            )
        case BotState.STOPPED | BotState.STOPPING:
            return _denied(
                request,
                code=RuntimeControlCode.RUNTIME_INVALID_TRANSITION,
                message="runtime is not accepting entries",
                next_action="Start the runtime before pausing entries.",
            )
        case unreachable:
            assert_never(unreachable)


def _resume(request: RuntimeControlRequest) -> RuntimeControlResult:
    match request.state:
        case BotState.PAUSED:
            gate = _resume_gate(request)
            if gate is not None:
                return gate
            return _accepted(
                request,
                state=BotState.RUNNING,
                message="runtime resumed after safety gates passed",
                next_action="Monitor runtime health before increasing risk.",
            )
        case BotState.RUNNING:
            return _denied(
                request,
                code=RuntimeControlCode.RUNTIME_ALREADY_RUNNING,
                message="runtime is already running",
                next_action="Use pause or stop if the run should change state.",
            )
        case BotState.STOPPED | BotState.STOPPING:
            return _denied(
                request,
                code=RuntimeControlCode.RUNTIME_INVALID_TRANSITION,
                message="runtime cannot resume from the current state",
                next_action="Start from stopped state after safety gates pass.",
            )
        case unreachable:
            assert_never(unreachable)


def _stop(request: RuntimeControlRequest) -> RuntimeControlResult:
    match request.state:
        case BotState.RUNNING | BotState.PAUSED | BotState.STOPPING:
            return _accepted(
                request,
                state=BotState.STOPPED,
                message="runtime stopped locally without live-order side effects",
                next_action="Inspect open positions before starting again.",
            )
        case BotState.STOPPED:
            return _denied(
                request,
                code=RuntimeControlCode.RUNTIME_ALREADY_STOPPED,
                message="runtime is already stopped",
                next_action="Use start after preflight and runtime health are clear.",
            )
        case unreachable:
            assert_never(unreachable)


def _resume_gate(request: RuntimeControlRequest) -> RuntimeControlResult | None:
    if request.settings.engine.live_trading:
        return _denied(
            request,
            code=RuntimeControlCode.RUNTIME_LIVE_UNSAFE,
            message="live trading runtime controls are not enabled in this milestone",
            next_action="Switch to paper/testnet or complete the live safety milestone.",
        )
    if request.readiness is None:
        return _denied(
            request,
            code=RuntimeControlCode.RUNTIME_PREFLIGHT_REQUIRED,
            message="preflight report is required before entries can run",
            next_action="Run preflight and fix blocked checks before starting.",
        )
    if request.readiness.blocked:
        return _denied(
            request,
            code=RuntimeControlCode.RUNTIME_PREFLIGHT_BLOCKED,
            message="preflight is blocking runtime entries",
            next_action="Open Settings and resolve blocked preflight checks.",
        )
    if request.health is None:
        return _denied(
            request,
            code=RuntimeControlCode.RUNTIME_HEALTH_REQUIRED,
            message="runtime health snapshot is required before entries can run",
            next_action="Refresh runtime health before starting or resuming.",
        )
    match request.health.state:
        case RuntimeHealthState.BLOCKED:
            return _denied(
                request,
                code=RuntimeControlCode.RUNTIME_HEALTH_BLOCKED,
                message="runtime health blocks new entries",
                next_action=request.health.next_action,
            )
        case RuntimeHealthState.HEALTHY | RuntimeHealthState.DEGRADED:
            return None
        case unreachable:
            assert_never(unreachable)


def _accepted(
    request: RuntimeControlRequest,
    *,
    state: BotState,
    message: str,
    next_action: str,
) -> RuntimeControlResult:
    return RuntimeControlResult(
        previous_state=request.state,
        state=state,
        command=request.command,
        accepted=True,
        code=RuntimeControlCode.RUNTIME_CONTROL_ACCEPTED,
        message=message,
        new_entries_allowed=new_entries_allowed(state),
        runtime_health_state=_health_state(request),
        next_action=next_action,
        live_orders_action=LIVE_ORDER_NOOP,
    )


def _denied(
    request: RuntimeControlRequest,
    *,
    code: RuntimeControlCode,
    message: str,
    next_action: str,
) -> RuntimeControlResult:
    return RuntimeControlResult(
        previous_state=request.state,
        state=request.state,
        command=request.command,
        accepted=False,
        code=code,
        message=message,
        new_entries_allowed=new_entries_allowed(request.state),
        runtime_health_state=_health_state(request),
        next_action=next_action,
        live_orders_action=LIVE_ORDER_NOOP,
    )


def _health_state(request: RuntimeControlRequest) -> RuntimeHealthState | None:
    if request.health is None:
        return None
    return request.health.state
