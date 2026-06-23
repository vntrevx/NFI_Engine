from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from nfi_engine.domain import AssetSymbol, TradingPair
from nfi_engine.strategy.errors import StrategyContractError, StrategyErrorCode
from nfi_engine.strategy.frame import StrategyFrame

BTC_ASSET: Final = AssetSymbol("BTC")


@dataclass(frozen=True, slots=True)
class PairFrame:
    pair: TradingPair
    timeframe: str
    frame: StrategyFrame
    stale: bool = False


@dataclass(frozen=True, slots=True)
class DataProviderFacade:
    frames: tuple[PairFrame, ...]

    def current_whitelist(self) -> tuple[str, ...]:
        whitelist: list[str] = []
        seen: set[str] = set()
        for pair_frame in self.frames:
            normalized = str(pair_frame.pair.normalized)
            if normalized not in seen:
                whitelist.append(normalized)
                seen.add(normalized)
        return tuple(whitelist)

    def available_timeframes(self, *, pair: TradingPair) -> tuple[str, ...]:
        timeframes: list[str] = []
        seen: set[str] = set()
        for pair_frame in self.frames:
            if pair_frame.pair == pair and pair_frame.timeframe not in seen:
                timeframes.append(pair_frame.timeframe)
                seen.add(pair_frame.timeframe)
        return tuple(timeframes)

    def btc_pair_for(self, pair: TradingPair) -> TradingPair:
        return TradingPair(base=BTC_ASSET, quote=pair.quote, settle=pair.settle)

    def get_pair_dataframe(self, *, pair: TradingPair, timeframe: str) -> StrategyFrame:
        return self._visible_frame(pair=pair, timeframe=timeframe)

    def get_informative_dataframe(self, *, pair: TradingPair, timeframe: str) -> StrategyFrame:
        return self._visible_frame(pair=pair, timeframe=timeframe)

    def get_btc_informative_dataframe(
        self,
        *,
        pair: TradingPair,
        timeframe: str,
    ) -> StrategyFrame:
        return self._visible_frame(pair=self.btc_pair_for(pair), timeframe=timeframe)

    def _visible_frame(self, *, pair: TradingPair, timeframe: str) -> StrategyFrame:
        pair_frame = self._find_pair_frame(pair=pair, timeframe=timeframe)
        if pair_frame.stale:
            raise StrategyContractError(
                code=StrategyErrorCode.DATA_PROVIDER_FRAME_STALE,
                message=f"strategy frame is stale for pair={pair.normalized} timeframe={timeframe}",
            )
        return pair_frame.frame.visible()

    def _find_pair_frame(self, *, pair: TradingPair, timeframe: str) -> PairFrame:
        for pair_frame in self.frames:
            if pair_frame.pair == pair and pair_frame.timeframe == timeframe:
                return pair_frame
        raise StrategyContractError(
            code=StrategyErrorCode.DATA_PROVIDER_FRAME_NOT_FOUND,
            message=f"no strategy frame for pair={pair.normalized} timeframe={timeframe}",
        )
