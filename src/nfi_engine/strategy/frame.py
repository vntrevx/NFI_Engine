from __future__ import annotations

from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Final, NewType, Self

from nfi_engine.strategy.errors import StrategyContractError, StrategyErrorCode

StrategyFeatureName = NewType("StrategyFeatureName", str)
MAX_FEATURES_PER_ROW: Final = 512
ZERO: Final = Decimal(0)


@dataclass(frozen=True, slots=True)
class SignalColumns:
    enter_long: bool = False
    enter_short: bool = False
    exit_long: bool = False
    exit_short: bool = False
    enter_tag: str | None = None
    exit_tag: str | None = None


@dataclass(frozen=True, slots=True)
class StrategyOhlcv:
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    @classmethod
    def from_close(cls, close: Decimal) -> Self:
        return cls(open=close, high=close, low=close, close=close, volume=ZERO)


@dataclass(frozen=True, slots=True)
class StrategyFeature:
    name: StrategyFeatureName
    value: Decimal


@dataclass(frozen=True, slots=True)
class StrategyRow:
    date: str
    close: Decimal
    ohlcv: StrategyOhlcv | None = None
    features: tuple[StrategyFeature, ...] = ()
    enter_long: bool = False
    enter_short: bool = False
    exit_long: bool = False
    exit_short: bool = False
    enter_tag: str | None = None
    exit_tag: str | None = None

    def __post_init__(self) -> None:
        ohlcv = StrategyOhlcv.from_close(self.close) if self.ohlcv is None else self.ohlcv
        if ohlcv.close != self.close:
            raise StrategyContractError(
                code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
                message="strategy row close must match OHLCV close",
            )
        object.__setattr__(self, "ohlcv", ohlcv)
        object.__setattr__(self, "features", _deduplicate_features(self.features))

    @property
    def open(self) -> Decimal:
        return self._ohlcv().open

    @property
    def high(self) -> Decimal:
        return self._ohlcv().high

    @property
    def low(self) -> Decimal:
        return self._ohlcv().low

    @property
    def volume(self) -> Decimal:
        return self._ohlcv().volume

    def feature(self, name: StrategyFeatureName) -> Decimal:
        for feature in self.features:
            if feature.name == name:
                return feature.value
        raise StrategyContractError(
            code=StrategyErrorCode.STRATEGY_FEATURE_NOT_FOUND,
            message=f"strategy feature is not available: {name}",
        )

    def with_feature(self, feature: StrategyFeature) -> Self:
        return replace(self, features=_upsert_feature(self.features, feature))

    def with_features(self, features: tuple[StrategyFeature, ...]) -> Self:
        if len(features) == 0:
            return self
        updated = _features_by_name(self.features)
        for feature in features:
            if feature.name not in updated and len(updated) >= MAX_FEATURES_PER_ROW:
                raise StrategyContractError(
                    code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
                    message="strategy row feature count exceeds the bounded feature budget",
                )
            updated[feature.name] = feature
        return replace(self, features=tuple(updated.values()))

    def with_signal(self, columns: SignalColumns) -> Self:
        return replace(
            self,
            enter_long=self.enter_long or columns.enter_long,
            enter_short=self.enter_short or columns.enter_short,
            exit_long=self.exit_long or columns.exit_long,
            exit_short=self.exit_short or columns.exit_short,
            enter_tag=columns.enter_tag if columns.enter_tag is not None else self.enter_tag,
            exit_tag=columns.exit_tag if columns.exit_tag is not None else self.exit_tag,
        )

    def _ohlcv(self) -> StrategyOhlcv:
        if self.ohlcv is None:
            return StrategyOhlcv.from_close(self.close)
        return self.ohlcv


@dataclass(frozen=True, slots=True)
class StrategyFrame:
    rows: tuple[StrategyRow, ...]
    visible_row_count: int | None = None

    def visible_rows(self) -> tuple[StrategyRow, ...]:
        return self.rows[: self._visible_count()]

    def last_visible_row(self) -> StrategyRow:
        visible_count = self._visible_count()
        if visible_count == 0:
            raise StrategyContractError(
                code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
                message="strategy frame has no visible rows",
            )
        return self.rows[visible_count - 1]

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

    def with_feature(self, *, index: int, feature: StrategyFeature) -> Self:
        visible_count = self._visible_count()
        normalized_index = _normalize_visible_index(index=index, visible_count=visible_count)
        updated_rows = tuple(
            row.with_feature(feature) if row_index == normalized_index else row
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


def _deduplicate_features(
    features: tuple[StrategyFeature, ...],
) -> tuple[StrategyFeature, ...]:
    deduplicated: dict[StrategyFeatureName, StrategyFeature] = {}
    for feature in features:
        if feature.name not in deduplicated and len(deduplicated) >= MAX_FEATURES_PER_ROW:
            raise StrategyContractError(
                code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
                message="strategy row feature count exceeds the bounded feature budget",
            )
        deduplicated[feature.name] = feature
    return tuple(deduplicated.values())


def _upsert_feature(
    features: tuple[StrategyFeature, ...],
    feature: StrategyFeature,
) -> tuple[StrategyFeature, ...]:
    updated = list(features)
    for index, existing in enumerate(updated):
        if existing.name == feature.name:
            updated[index] = feature
            return tuple(updated)
    if len(features) >= MAX_FEATURES_PER_ROW:
        raise StrategyContractError(
            code=StrategyErrorCode.STRATEGY_CONTRACT_ERROR,
            message="strategy row feature count exceeds the bounded feature budget",
        )
    return (*features, feature)


def _features_by_name(
    features: tuple[StrategyFeature, ...],
) -> dict[StrategyFeatureName, StrategyFeature]:
    return {feature.name: feature for feature in features}
