from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Final, Self

from nfi_engine.domain import Leverage, PositionSide, SignalType, TradingPair
from nfi_engine.strategy.dtos import StrategyInspection, StrategyMetadata, StrategySignal
from nfi_engine.strategy.errors import StrategyContractError, StrategyErrorCode
from nfi_engine.strategy.frame import StrategyFrame, StrategyRow
from nfi_engine.strategy.protocols import LeverageCallback, RequiredFreqtradeStrategy

CALLBACK_NAMES: Final = (
    "populate_indicators",
    "populate_entry_trend",
    "populate_exit_trend",
    "informative_pairs",
    "custom_exit",
    "custom_stake_amount",
    "order_filled",
    "adjust_trade_position",
    "confirm_trade_entry",
    "confirm_trade_exit",
    "bot_loop_start",
    "leverage",
)


@dataclass(frozen=True, slots=True)
class FreqtradeStrategyAdapter:
    strategy: RequiredFreqtradeStrategy

    @classmethod
    def from_strategy(cls, strategy: object) -> Self:
        if not isinstance(strategy, RequiredFreqtradeStrategy):
            raise StrategyContractError(
                code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
                message=(
                    "strategy must define timeframe, can_short, populate_indicators, "
                    "populate_entry_trend, and populate_exit_trend"
                ),
            )
        return cls(strategy=strategy)

    def inspect(self) -> StrategyInspection:
        return StrategyInspection(
            name=type(self.strategy).__name__,
            can_short=self.strategy.can_short,
            timeframe=self.strategy.timeframe,
            detected_callbacks=tuple(
                callback_name
                for callback_name in CALLBACK_NAMES
                if callable(getattr(self.strategy, callback_name, None))
            ),
        )

    def analyze(
        self,
        frame: StrategyFrame,
        metadata: StrategyMetadata,
        *,
        incremental: bool,
    ) -> tuple[StrategySignal, ...]:
        visible_frame = frame if incremental else frame.visible()
        indicator_frame = self.strategy.populate_indicators(visible_frame, metadata)
        entry_frame = self.strategy.populate_entry_trend(indicator_frame, metadata)
        exit_frame = self.strategy.populate_exit_trend(entry_frame, metadata)
        return _signals_from_row(row=exit_frame.last_visible_row(), metadata=metadata)

    def leverage(self, pair: TradingPair, current_leverage: Leverage) -> Leverage:
        if isinstance(self.strategy, LeverageCallback):
            return self.strategy.leverage(pair, current_leverage)
        return current_leverage


def load_freqtrade_strategy(spec: str) -> RequiredFreqtradeStrategy:
    module_name, separator, class_name = spec.partition(":")
    if separator == "" or module_name == "" or class_name == "":
        raise StrategyContractError(
            code=StrategyErrorCode.STRATEGY_LOAD_ERROR,
            message="strategy spec must use module.path:ClassName",
        )
    module = _import_strategy_module(module_name)
    candidate = _get_module_attribute(module=module, attribute_name=class_name)
    if not isinstance(candidate, type):
        raise StrategyContractError(
            code=StrategyErrorCode.STRATEGY_LOAD_ERROR,
            message=f"strategy class not found: {spec}",
        )
    candidate_type: type[object] = candidate
    try:
        strategy: object = candidate_type()
    except TypeError as exc:
        raise StrategyContractError(
            code=StrategyErrorCode.STRATEGY_LOAD_ERROR,
            message=f"strategy class must be constructable without arguments: {spec}",
        ) from exc
    return _require_freqtrade_strategy(strategy)


def _import_strategy_module(module_name: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except ImportError:
        _ensure_cwd_on_import_path()
    try:
        return importlib.import_module(module_name)
    except ImportError as exc:
        raise StrategyContractError(
            code=StrategyErrorCode.STRATEGY_LOAD_ERROR,
            message=f"strategy module could not be imported: {module_name}",
        ) from exc


def _ensure_cwd_on_import_path() -> None:
    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)


def _get_module_attribute(*, module: ModuleType, attribute_name: str) -> object | None:
    attribute: object | None = getattr(module, attribute_name, None)
    return attribute


def _require_freqtrade_strategy(strategy: object) -> RequiredFreqtradeStrategy:
    if isinstance(strategy, RequiredFreqtradeStrategy):
        return strategy
    raise StrategyContractError(
        code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
        message=(
            "strategy must define timeframe, can_short, populate_indicators, "
            "populate_entry_trend, and populate_exit_trend"
        ),
    )


def _signals_from_row(
    *,
    row: StrategyRow,
    metadata: StrategyMetadata,
) -> tuple[StrategySignal, ...]:
    signals: list[StrategySignal] = []
    if row.enter_long:
        signals.append(
            StrategySignal(
                pair=metadata.pair,
                side=PositionSide.LONG,
                signal_type=SignalType.ENTER,
                tag=row.enter_tag,
            ),
        )
    if row.enter_short:
        signals.append(
            StrategySignal(
                pair=metadata.pair,
                side=PositionSide.SHORT,
                signal_type=SignalType.ENTER,
                tag=row.enter_tag,
            ),
        )
    if row.exit_long:
        signals.append(
            StrategySignal(
                pair=metadata.pair,
                side=PositionSide.LONG,
                signal_type=SignalType.EXIT,
            ),
        )
    if row.exit_short:
        signals.append(
            StrategySignal(
                pair=metadata.pair,
                side=PositionSide.SHORT,
                signal_type=SignalType.EXIT,
            ),
        )
    return tuple(signals)
