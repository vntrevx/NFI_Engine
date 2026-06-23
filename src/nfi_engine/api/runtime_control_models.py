from __future__ import annotations

from nfi_engine.api.models import StrictApiModel
from nfi_engine.paper import BotState
from nfi_engine.runtime_control import RuntimeControlResult, new_entries_allowed


class RuntimeControlCommandRequest(StrictApiModel):
    command: str | None = None


class RuntimeControlResponse(StrictApiModel):
    previous_state: BotState
    state: BotState
    command: str | None
    accepted: bool
    code: str
    message: str
    new_entries_allowed: bool
    runtime_health_state: str | None
    next_action: str
    live_orders_action: str

    @classmethod
    def from_result(cls, result: RuntimeControlResult) -> RuntimeControlResponse:
        health_state = (
            None if result.runtime_health_state is None else result.runtime_health_state.value
        )
        return cls(
            previous_state=result.previous_state,
            state=result.state,
            command=result.command.value,
            accepted=result.accepted,
            code=result.code.value,
            message=result.message,
            new_entries_allowed=result.new_entries_allowed,
            runtime_health_state=health_state,
            next_action=result.next_action,
            live_orders_action=result.live_orders_action,
        )

    @classmethod
    def from_state(cls, state: BotState) -> RuntimeControlResponse:
        return cls(
            previous_state=state,
            state=state,
            command=None,
            accepted=True,
            code="RUNTIME_CONTROL_STATE",
            message="runtime control state snapshot",
            new_entries_allowed=new_entries_allowed(state),
            runtime_health_state=None,
            next_action="Use start, pause, resume, or stop through protected controls.",
            live_orders_action="No live exchange order cancellation is performed by this control.",
        )
