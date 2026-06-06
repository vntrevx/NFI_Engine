from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, ConfigDict, ValidationError

from nfi_engine.domain import DomainError, PositionSide, Price, TradingMode, TradingPair
from nfi_engine.paper.errors import PaperError, PaperErrorCode
from nfi_engine.paper.models import PaperTick


class PaperTickPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="forbid", frozen=True)

    pair: str
    at: datetime
    price: Decimal
    signal_side: PositionSide | None = None


def load_paper_ticks(path: Path, trading_mode: TradingMode) -> tuple[PaperTick, ...]:
    try:
        return tuple(
            _tick_from_payload(PaperTickPayload.model_validate_json(line), trading_mode)
            for line in _lines(path)
        )
    except (ValidationError, DomainError) as exc:
        raise PaperError(
            code=PaperErrorCode.TICK_PARSE_ERROR,
            message=str(exc),
        ) from exc


def _lines(path: Path) -> tuple[str, ...]:
    return tuple(
        line for line in path.read_text(encoding="utf-8").splitlines() if line.strip() != ""
    )


def _tick_from_payload(payload: PaperTickPayload, trading_mode: TradingMode) -> PaperTick:
    return PaperTick(
        pair=TradingPair.parse(payload.pair, trading_mode),
        at=payload.at,
        price=Price(payload.price),
        signal_side=payload.signal_side,
    )
