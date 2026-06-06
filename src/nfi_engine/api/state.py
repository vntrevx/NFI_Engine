from __future__ import annotations

from dataclasses import dataclass
from typing import assert_never

from nfi_engine.config import RuntimeSettings
from nfi_engine.paper import BotCommand, BotState, apply_bot_command


@dataclass(slots=True)
class ApiRuntimeState:
    """Mutable because REST control endpoints must share current bot state."""

    state: BotState = BotState.STOPPED

    def apply(self, command: BotCommand) -> BotState:
        match command:
            case BotCommand.START | BotCommand.PAUSE | BotCommand.RESUME:
                self.state = apply_bot_command(self.state, command)
            case BotCommand.STOP:
                self.state = apply_bot_command(self.state, command)
                self.state = apply_bot_command(self.state, command)
            case unreachable:
                assert_never(unreachable)
        return self.state


@dataclass(frozen=True, slots=True)
class ApiContext:
    settings: RuntimeSettings
    runtime: ApiRuntimeState
