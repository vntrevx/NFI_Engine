from __future__ import annotations

from nfi_engine.paper import BotCommand, BotState, apply_bot_command


def test_bot_lifecycle_transitions_start_pause_resume_and_stop() -> None:
    # Given
    state = BotState.STOPPED

    # When
    running = apply_bot_command(state, BotCommand.START)
    paused = apply_bot_command(running, BotCommand.PAUSE)
    resumed = apply_bot_command(paused, BotCommand.RESUME)
    stopping = apply_bot_command(resumed, BotCommand.STOP)
    stopped = apply_bot_command(stopping, BotCommand.STOP)

    # Then
    assert (running, paused, resumed, stopping, stopped) == (
        BotState.RUNNING,
        BotState.PAUSED,
        BotState.RUNNING,
        BotState.STOPPING,
        BotState.STOPPED,
    )
