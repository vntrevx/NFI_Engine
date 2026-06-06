from __future__ import annotations

from datetime import datetime

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import Leverage, TradingPair
from nfi_engine.risk.models import PairLock, RiskPolicy


def policy_from_runtime(settings: RuntimeSettings) -> RiskPolicy:
    return RiskPolicy(
        trading_mode=settings.exchange.trading_mode,
        max_open_trades=settings.risk.max_open_trades,
        max_leverage=Leverage.parse(settings.risk.max_leverage),
        stoploss_pct=settings.risk.stoploss_pct,
        minimal_roi=settings.risk.minimal_roi,
        paper_trading=settings.paper_run.enabled,
        testnet=settings.exchange.testnet,
        live_trading=settings.engine.live_trading,
    )


def pair_locks_from_runtime(
    *,
    settings: RuntimeSettings,
    current_time: datetime,
) -> tuple[PairLock, ...]:
    locked_pairs = tuple(_split_locked_pairs(settings.risk.locked_pairs))
    return tuple(
        PairLock(
            pair=TradingPair.parse(pair, settings.exchange.trading_mode),
            reason="configured lock",
            expires_at=current_time,
        )
        for pair in locked_pairs
    )


def _split_locked_pairs(raw: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in raw.split(",") if item.strip() != "")
