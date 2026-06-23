from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from nfi_engine.config import RuntimeSettings
from nfi_engine.paper import BotState

if TYPE_CHECKING:
    from nfi_engine.dashboard import DashboardReadStore
    from nfi_engine.wallet import WalletBalanceReader


@dataclass(slots=True)
class ApiRuntimeState:
    """Mutable because REST control endpoints must share current bot state."""

    state: BotState = BotState.STOPPED

    def set_state(self, state: BotState) -> None:
        self.state = state


@dataclass(slots=True)
class ApiContext:
    settings: RuntimeSettings
    runtime: ApiRuntimeState
    dashboard_store: DashboardReadStore
    wallet_balance_reader: WalletBalanceReader | None = None
    config_path: Path | None = None
