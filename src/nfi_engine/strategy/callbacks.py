from __future__ import annotations

from typing import Final

from nfi_engine.strategy.dtos import CallbackSupportLevel, StrategyCallbackSupport
from nfi_engine.strategy.protocols import RequiredFreqtradeStrategy

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
UNKNOWN_CALLBACK_PREFIXES: Final = ("custom_", "confirm_", "adjust_", "check_", "order_", "bot_")

SUPPORTED_CALLBACKS: Final = frozenset(
    (
        "populate_indicators",
        "populate_entry_trend",
        "populate_exit_trend",
    ),
)
PARTIAL_CALLBACKS: Final = frozenset(
    callback_name for callback_name in CALLBACK_NAMES if callback_name not in SUPPORTED_CALLBACKS
)
SUPPORTED_REASON: Final = "implemented in the clean-room strategy adapter contract"
PARTIAL_REASON: Final = "detected and reported; full runtime behavior requires fixture evidence"
EXCLUDED_REASON: Final = "outside the current clean-room callback contract"


def detect_known_callbacks(strategy: RequiredFreqtradeStrategy) -> tuple[str, ...]:
    return tuple(
        callback_name
        for callback_name in CALLBACK_NAMES
        if _has_callable_attribute(strategy=strategy, attribute_name=callback_name)
    )


def build_callback_support(
    strategy: RequiredFreqtradeStrategy,
) -> tuple[StrategyCallbackSupport, ...]:
    known = tuple(
        _known_callback_support(strategy=strategy, callback_name=callback_name)
        for callback_name in CALLBACK_NAMES
    )
    excluded = tuple(
        StrategyCallbackSupport(
            name=callback_name,
            level=CallbackSupportLevel.EXCLUDED,
            detected=True,
            reason=EXCLUDED_REASON,
        )
        for callback_name in _unknown_public_callbacks(strategy)
    )
    return (*known, *excluded)


def _known_callback_support(
    *,
    strategy: RequiredFreqtradeStrategy,
    callback_name: str,
) -> StrategyCallbackSupport:
    level = _known_callback_level(callback_name)
    return StrategyCallbackSupport(
        name=callback_name,
        level=level,
        detected=_has_callable_attribute(strategy=strategy, attribute_name=callback_name),
        reason=_reason_for_level(level),
    )


def _known_callback_level(callback_name: str) -> CallbackSupportLevel:
    if callback_name in SUPPORTED_CALLBACKS:
        return CallbackSupportLevel.SUPPORTED
    return CallbackSupportLevel.PARTIAL


def _reason_for_level(level: CallbackSupportLevel) -> str:
    match level:
        case CallbackSupportLevel.SUPPORTED:
            return SUPPORTED_REASON
        case CallbackSupportLevel.PARTIAL:
            return PARTIAL_REASON
        case CallbackSupportLevel.EXCLUDED:
            return EXCLUDED_REASON


def _unknown_public_callbacks(strategy: RequiredFreqtradeStrategy) -> tuple[str, ...]:
    known = frozenset(CALLBACK_NAMES)
    return tuple(
        attribute_name
        for attribute_name in sorted(dir(strategy))
        if attribute_name not in known
        and not attribute_name.startswith("_")
        and attribute_name.startswith(UNKNOWN_CALLBACK_PREFIXES)
        and _has_callable_attribute(strategy=strategy, attribute_name=attribute_name)
    )


def _has_callable_attribute(
    *,
    strategy: RequiredFreqtradeStrategy,
    attribute_name: str,
) -> bool:
    return callable(getattr(strategy, attribute_name, None))
