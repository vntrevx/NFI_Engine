from __future__ import annotations

import importlib
import sys

from nfi_engine.domain import Leverage, TradingMode, TradingPair
from nfi_engine.strategy.nfi_x7 import (
    X7_DATA_REQUIREMENTS,
    build_x7_import_profile,
    build_x7_resource_budget,
)
from nfi_engine.strategy.nfi_x7.strategy import X7_DEFAULT_LEVERAGE, X7NativeStrategy

PACKAGE_NAME = "nfi_engine.strategy.nfi_x7"
PACKAGE_PREFIX = f"{PACKAGE_NAME}."
FORBIDDEN_RUNTIME_MODULES = ("freqtrade", "pandas", "rapidjson", "talib")


def test_import_profile_reports_injected_forbidden_runtime_modules() -> None:
    # Given
    loaded_module_names = (
        "json",
        "nfi_engine.strategy.nfi_x7",
        "pandas.core.frame",
        "freqtrade.exchange.exchange",
        "talib.abstract",
        "rapidjson",
    )

    # When
    profile = build_x7_import_profile(loaded_module_names)

    # Then
    assert profile.forbidden_runtime_modules == FORBIDDEN_RUNTIME_MODULES
    assert profile.loaded_forbidden_runtime_modules == (
        "freqtrade",
        "pandas",
        "rapidjson",
        "talib",
    )
    assert profile.has_forbidden_runtime_modules_loaded is True


def test_current_native_x7_import_has_no_forbidden_runtime_modules() -> None:
    # Given
    _clear_x7_modules()
    loaded_before_import = set(sys.modules)

    # When
    importlib.import_module(PACKAGE_NAME)
    loaded_after_import = set(sys.modules)
    profile = build_x7_import_profile(
        tuple(sorted(loaded_after_import - loaded_before_import)),
    )

    # Then
    assert profile.loaded_forbidden_runtime_modules == ()
    assert profile.has_forbidden_runtime_modules_loaded is False


def test_resource_budget_reports_native_x7_runtime_constraints() -> None:
    # Given
    strategy = X7NativeStrategy()
    pair = TradingPair.parse("ETH/USDT:USDT", TradingMode.FUTURES)

    # When
    budget = build_x7_resource_budget()
    leverage = strategy.leverage(pair, Leverage.one())

    # Then
    assert budget.mandatory_external_dependencies == ()
    assert budget.pi4_public_claim_requires_hardware_evidence is True
    assert budget.precomputed_leverage is True
    assert budget.feature_graph_feature_budget == 64
    assert budget.feature_graph_cache_limit == 4
    assert leverage is X7_DEFAULT_LEVERAGE
    assert budget.informative_timeframe_count == len(X7_DATA_REQUIREMENTS.informative_timeframes)
    assert budget.informative_timeframe_count == 4
    assert budget.bounded_timeframe_count == 1 + len(X7_DATA_REQUIREMENTS.informative_timeframes)
    assert budget.structure_backend == "local_typed_structures"


def _clear_x7_modules() -> None:
    for module_name in tuple(sys.modules):
        if module_name == PACKAGE_NAME or module_name.startswith(PACKAGE_PREFIX):
            sys.modules.pop(module_name)
