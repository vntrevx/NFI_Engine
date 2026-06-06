from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict

from nfi_engine.domain import Price, TradingMode, TradingPair
from nfi_engine.exchange.models import Tick


class TickPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    pair: str
    at: datetime
    price: Decimal
    funding_rate: Decimal | None = None


def load_tick_fixture(path: Path, trading_mode: TradingMode) -> tuple[Tick, ...]:
    return tuple(
        _tick_from_payload(TickPayload.model_validate_json(line), trading_mode)
        for line in _lines(path)
    )


def _lines(path: Path) -> tuple[str, ...]:
    return tuple(
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip() != ""
    )


def _tick_from_payload(payload: TickPayload, trading_mode: TradingMode) -> Tick:
    return Tick(
        pair=TradingPair.parse(payload.pair, trading_mode),
        price=Price(payload.price),
        at=payload.at,
        funding_rate=payload.funding_rate,
    )
