from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Self

from nfi_engine.domain import TradingPair
from nfi_engine.strategy.errors import StrategyContractError, StrategyErrorCode


@dataclass(frozen=True, slots=True)
class SignalColumns:
    enter_long: bool = False
    enter_short: bool = False
    exit_long: bool = False
    exit_short: bool = False
    enter_tag: str | None = None


@dataclass(frozen=True, slots=True)
class StrategyRow:
    date: str
    close: Decimal
    enter_long: bool = False
    enter_short: bool = False
    exit_long: bool = False
    exit_short: bool = False
    enter_tag: str | None = None

    def with_signal(self, columns: SignalColumns) -> Self:
        return type(self)(
            date=self.date,
            close=self.close,
            enter_long=self.enter_long or columns.enter_long,
            enter_short=self.enter_short or columns.enter_short,
            exit_long=self.exit_long or columns.exit_long,
            exit_short=self.exit_short or columns.exit_short,
            enter_tag=columns.enter_tag if columns.enter_tag is not None else self.enter_tag,
        )


@dataclass(frozen=True, slots=True)
class StrategyFrame:
    rows: tuple[StrategyRow, ...]
    visible_row_count: int | None = None

    def visible_rows(self) -> tuple[StrategyRow, ...]:
        return self.rows[: self._visible_count()]

    def last_visible_row(self) -> StrategyRow:
        visible = self.visible_rows()
        if len(visible) == 0:
            raise StrategyContractError(
                code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
                message="strategy frame has no visible rows",
            )
        return visible[-1]

    def visible(self) -> Self:
        return type(self)(rows=self.visible_rows())

    def future_rows(self) -> tuple[StrategyRow, ...]:
        visible_count = self._visible_count()
        if visible_count < len(self.rows):
            raise StrategyContractError(
                code=StrategyErrorCode.LOOKAHEAD_ACCESS,
                message="strategy attempted to read rows beyond the incremental cursor",
            )
        return ()

    def with_signal(self, *, index: int, columns: SignalColumns) -> Self:
        visible_count = self._visible_count()
        normalized_index = _normalize_visible_index(index=index, visible_count=visible_count)
        updated_rows = tuple(
            row.with_signal(columns) if row_index == normalized_index else row
            for row_index, row in enumerate(self.rows)
        )
        return type(self)(rows=updated_rows, visible_row_count=self.visible_row_count)

    def _visible_count(self) -> int:
        if self.visible_row_count is None:
            return len(self.rows)
        if self.visible_row_count < 0 or self.visible_row_count > len(self.rows):
            raise StrategyContractError(
                code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
                message="visible_row_count must be inside the strategy frame row bounds",
            )
        return self.visible_row_count


@dataclass(frozen=True, slots=True)
class PairFrame:
    pair: TradingPair
    timeframe: str
    frame: StrategyFrame


@dataclass(frozen=True, slots=True)
class DataProviderFacade:
    frames: tuple[PairFrame, ...]

    def current_whitelist(self) -> tuple[str, ...]:
        return tuple(pair_frame.pair.normalized for pair_frame in self.frames)

    def get_pair_dataframe(self, *, pair: TradingPair, timeframe: str) -> StrategyFrame:
        for pair_frame in self.frames:
            if pair_frame.pair == pair and pair_frame.timeframe == timeframe:
                return pair_frame.frame.visible()
        raise StrategyContractError(
            code=StrategyErrorCode.DATA_PROVIDER_FRAME_NOT_FOUND,
            message=f"no strategy frame for pair={pair.normalized} timeframe={timeframe}",
        )


def _normalize_visible_index(*, index: int, visible_count: int) -> int:
    if visible_count == 0:
        raise StrategyContractError(
            code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
            message="cannot write signal into an empty visible frame",
        )
    normalized_index = visible_count + index if index < 0 else index
    if normalized_index < 0 or normalized_index >= visible_count:
        raise StrategyContractError(
            code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
            message="signal index must target a visible row",
        )
    return normalized_index
