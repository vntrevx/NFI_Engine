from __future__ import annotations

from types import MappingProxyType
from typing import Final

from nfi_engine.paper.models import BotCommand, BotState

TRANSITIONS: Final = MappingProxyType(
    {
        (BotState.STOPPED, BotCommand.START): BotState.RUNNING,
        (BotState.RUNNING, BotCommand.PAUSE): BotState.PAUSED,
        (BotState.PAUSED, BotCommand.RESUME): BotState.RUNNING,
        (BotState.RUNNING, BotCommand.STOP): BotState.STOPPING,
        (BotState.PAUSED, BotCommand.STOP): BotState.STOPPING,
        (BotState.STOPPING, BotCommand.STOP): BotState.STOPPED,
    },
)


def apply_bot_command(state: BotState, command: BotCommand) -> BotState:
    return TRANSITIONS.get((state, command), state)
