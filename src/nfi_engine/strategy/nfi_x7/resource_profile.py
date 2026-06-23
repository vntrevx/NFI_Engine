from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Final

from nfi_engine.strategy.nfi_x7.feature_graph_models import (
    X7_FEATURE_GRAPH_CACHE_LIMIT,
    X7_FEATURE_GRAPH_FEATURE_BUDGET,
)
from nfi_engine.strategy.nfi_x7.requirements import X7_DATA_REQUIREMENTS

FORBIDDEN_RUNTIME_MODULES: Final = ("freqtrade", "pandas", "rapidjson", "talib")
LOCAL_TYPED_STRUCTURES_BACKEND: Final = "local_typed_structures"
PRECOMPUTED_LEVERAGE_AVAILABLE: Final = True
PI4_PUBLIC_CLAIM_REQUIRES_HARDWARE_EVIDENCE: Final = True


@dataclass(frozen=True, slots=True)
class X7ImportProfile:
    forbidden_runtime_modules: tuple[str, ...]
    loaded_forbidden_runtime_modules: tuple[str, ...]
    has_forbidden_runtime_modules_loaded: bool


@dataclass(frozen=True, slots=True)
class X7ResourceBudget:
    mandatory_external_dependencies: tuple[str, ...]
    structure_backend: str
    precomputed_leverage: bool
    feature_graph_feature_budget: int
    feature_graph_cache_limit: int
    informative_timeframe_count: int
    bounded_timeframe_count: int
    pi4_public_claim_requires_hardware_evidence: bool


def build_x7_import_profile(loaded_module_names: Iterable[str]) -> X7ImportProfile:
    normalized_loaded_module_names = tuple(loaded_module_names)
    loaded_forbidden_runtime_modules = tuple(
        forbidden_module
        for forbidden_module in FORBIDDEN_RUNTIME_MODULES
        if _module_is_loaded(normalized_loaded_module_names, forbidden_module)
    )
    return X7ImportProfile(
        forbidden_runtime_modules=FORBIDDEN_RUNTIME_MODULES,
        loaded_forbidden_runtime_modules=loaded_forbidden_runtime_modules,
        has_forbidden_runtime_modules_loaded=bool(loaded_forbidden_runtime_modules),
    )


def build_x7_resource_budget() -> X7ResourceBudget:
    informative_timeframes = X7_DATA_REQUIREMENTS.informative_timeframes
    bounded_timeframe_count = 1 + len(informative_timeframes)
    return X7ResourceBudget(
        mandatory_external_dependencies=X7_DATA_REQUIREMENTS.mandatory_external_dependencies,
        structure_backend=LOCAL_TYPED_STRUCTURES_BACKEND,
        precomputed_leverage=PRECOMPUTED_LEVERAGE_AVAILABLE,
        feature_graph_feature_budget=X7_FEATURE_GRAPH_FEATURE_BUDGET,
        feature_graph_cache_limit=X7_FEATURE_GRAPH_CACHE_LIMIT,
        informative_timeframe_count=len(informative_timeframes),
        bounded_timeframe_count=bounded_timeframe_count,
        pi4_public_claim_requires_hardware_evidence=PI4_PUBLIC_CLAIM_REQUIRES_HARDWARE_EVIDENCE,
    )


def _module_is_loaded(
    loaded_module_names: tuple[str, ...],
    forbidden_module: str,
) -> bool:
    dotted_forbidden_module = f"{forbidden_module}."
    return any(
        loaded_module_name == forbidden_module
        or loaded_module_name.startswith(dotted_forbidden_module)
        for loaded_module_name in loaded_module_names
    )
