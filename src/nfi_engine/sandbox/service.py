from __future__ import annotations

import sys
from dataclasses import dataclass
from importlib import util as importlib_util
from pathlib import Path

from nfi_engine.sandbox.errors import SandboxError, SandboxErrorCode
from nfi_engine.sandbox.models import APPROVED_CAPABILITIES, SandboxCheckResult
from nfi_engine.sandbox.scanner import scan_strategy_source
from nfi_engine.strategy import FreqtradeStrategyAdapter, load_freqtrade_strategy


@dataclass(frozen=True, slots=True)
class StrategySpec:
    module_name: str
    class_name: str


def check_strategy_sandbox(strategy_spec: str) -> SandboxCheckResult:
    spec = _parse_strategy_spec(strategy_spec)
    source_path = _resolve_strategy_source(spec.module_name)
    violations = scan_strategy_source(source_path, class_name=spec.class_name)
    if len(violations) > 0:
        return SandboxCheckResult(
            strategy_spec=strategy_spec,
            passed=False,
            approved_capabilities=APPROVED_CAPABILITIES,
            violations=violations,
        )
    strategy = load_freqtrade_strategy(strategy_spec)
    inspection = FreqtradeStrategyAdapter.from_strategy(strategy).inspect()
    return SandboxCheckResult(
        strategy_spec=strategy_spec,
        passed=True,
        approved_capabilities=APPROVED_CAPABILITIES,
        violations=(),
        detected_callbacks=inspection.detected_callbacks,
    )


def _parse_strategy_spec(raw: str) -> StrategySpec:
    module_name, separator, class_name = raw.partition(":")
    if separator == "" or module_name == "" or class_name == "":
        raise SandboxError(
            code=SandboxErrorCode.SANDBOX_STRATEGY_LOAD_ERROR,
            message="strategy spec must use module.path:ClassName",
        )
    return StrategySpec(module_name=module_name, class_name=class_name)


def _resolve_strategy_source(module_name: str) -> Path:
    _ensure_cwd_on_import_path()
    spec = importlib_util.find_spec(module_name)
    if spec is None or spec.origin is None:
        raise SandboxError(
            code=SandboxErrorCode.SANDBOX_STRATEGY_LOAD_ERROR,
            message=f"strategy module source not found: {module_name}",
        )
    return Path(spec.origin)


def _ensure_cwd_on_import_path() -> None:
    cwd = str(Path.cwd())
    if cwd not in sys.path:
        sys.path.insert(0, cwd)
