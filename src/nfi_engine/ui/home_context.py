from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from nfi_engine.dashboard import DashboardReadModels
from nfi_engine.paper import BotState

if TYPE_CHECKING:
    from nfi_engine.preflight.models import PreflightReport
    from nfi_engine.runtime_health import RuntimeHealthSnapshot
    from nfi_engine.wallet import WalletBalanceSnapshot


@dataclass(frozen=True, slots=True)
class HomeRuntimeContext:
    read_models: DashboardReadModels | None = None
    readiness: PreflightReport | None = None
    wallet_balance: WalletBalanceSnapshot | None = None
    runtime_health: RuntimeHealthSnapshot | None = None
    bot_state: BotState = BotState.STOPPED
