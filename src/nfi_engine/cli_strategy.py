from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, ClassVar, Final, NoReturn

import typer
from pydantic import BaseModel, ConfigDict

from nfi_engine.config import ConfigLoadError, RuntimeSettings, load_runtime_settings
from nfi_engine.strategy import (
    FreqtradeStrategyAdapter,
    StrategyContractError,
    load_freqtrade_strategy,
)
from nfi_engine.strategy.nfi_x7 import (
    X7CoverageReport,
    X7NativeStrategy,
    X7SemanticStatus,
    build_x7_coverage_report,
    build_x7_semantic_status,
)

strategy_app: Final[typer.Typer] = typer.Typer(help="Inspect strategy adapter contracts.")


class CoverageModulePayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    name: str
    status: str
    evidence_path: str
    blocker: str | None


class CoverageReportPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    covered_modules: tuple[str, ...]
    pending_modules: tuple[str, ...]
    is_full_semantic_coverage: bool
    modules: tuple[CoverageModulePayload, ...]


class X7SemanticStatusPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    enabled: bool
    coverage_state: str
    observed_upstream_version: str
    provenance_evidence_path: str
    covered_modules: tuple[str, ...]
    pending_modules: tuple[str, ...]
    latest_signal_reason: str
    warmup_state: str
    missing_data_state: str
    live_readiness: str
    blocked_reason: str | None
    next_action: str


class StrategyInspectPayload(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True)

    strategy_name: str
    can_short: bool
    timeframe: str
    callbacks: tuple[str, ...]
    semantic_coverage: CoverageReportPayload | None
    x7_semantic_status: X7SemanticStatusPayload | None


@strategy_app.command("inspect")
def inspect_strategy(
    strategy: Annotated[str, typer.Option("--strategy")],
    config: Annotated[Path, typer.Option("--config", exists=True, dir_okay=False)],
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    try:
        settings = load_runtime_settings(config)
        loaded_strategy = load_freqtrade_strategy(strategy)
        inspection = FreqtradeStrategyAdapter.from_strategy(loaded_strategy).inspect()
    except ConfigLoadError as exc:
        _exit_with_config_error(exc)
    except StrategyContractError as exc:
        _exit_with_strategy_error(exc)
    if json_output:
        payload = _inspect_payload(
            _InspectionPayloadInput(
                strategy=loaded_strategy,
                strategy_name=inspection.name,
                can_short=inspection.can_short,
                timeframe=inspection.timeframe,
                callbacks=inspection.detected_callbacks,
                settings=settings,
            ),
        )
        sys.stdout.write(payload.model_dump_json(indent=2))
        sys.stdout.write("\n")
        return
    sys.stdout.write(
        "\n".join(
            (
                f"strategy_name={inspection.name}",
                f"can_short={str(inspection.can_short).lower()}",
                f"timeframe={inspection.timeframe}",
                f"callbacks={_format_callbacks(inspection.detected_callbacks)}",
            ),
        ),
    )
    sys.stdout.write("\n")


@dataclass(frozen=True, slots=True)
class _InspectionPayloadInput:
    strategy: object
    strategy_name: str
    can_short: bool
    timeframe: str
    callbacks: tuple[str, ...]
    settings: RuntimeSettings


def _inspect_payload(payload_input: _InspectionPayloadInput) -> StrategyInspectPayload:
    coverage_report = _x7_coverage_report(payload_input.strategy)
    return StrategyInspectPayload(
        strategy_name=payload_input.strategy_name,
        can_short=payload_input.can_short,
        timeframe=payload_input.timeframe,
        callbacks=payload_input.callbacks,
        semantic_coverage=_coverage_payload(coverage_report)
        if coverage_report is not None
        else None,
        x7_semantic_status=_x7_status_payload(
            strategy=payload_input.strategy,
            settings=payload_input.settings,
            coverage_report=coverage_report,
        ),
    )


def _x7_coverage_report(strategy: object) -> X7CoverageReport | None:
    if not isinstance(strategy, X7NativeStrategy):
        return None
    return build_x7_coverage_report()


def _coverage_payload(report: X7CoverageReport) -> CoverageReportPayload:
    return CoverageReportPayload(
        covered_modules=report.covered_modules,
        pending_modules=report.pending_modules,
        is_full_semantic_coverage=report.is_full_semantic_coverage,
        modules=tuple(
            CoverageModulePayload(
                name=module.name,
                status=module.status.value,
                evidence_path=module.evidence_path,
                blocker=module.blocker,
            )
            for module in report.modules
        ),
    )


def _x7_status_payload(
    *,
    strategy: object,
    settings: RuntimeSettings,
    coverage_report: X7CoverageReport | None,
) -> X7SemanticStatusPayload | None:
    if not isinstance(strategy, X7NativeStrategy) or coverage_report is None:
        return None
    status = build_x7_semantic_status(
        settings=settings,
        readiness=None,
        coverage_report=coverage_report,
    )
    return _status_payload(status)


def _status_payload(status: X7SemanticStatus) -> X7SemanticStatusPayload:
    return X7SemanticStatusPayload(
        enabled=status.enabled,
        coverage_state=status.coverage_state.value,
        observed_upstream_version=status.observed_upstream_version,
        provenance_evidence_path=status.provenance_evidence_path,
        covered_modules=status.covered_modules,
        pending_modules=status.pending_modules,
        latest_signal_reason=status.latest_signal_reason,
        warmup_state=status.warmup_state,
        missing_data_state=status.missing_data_state,
        live_readiness=status.live_readiness.value,
        blocked_reason=status.blocked_reason,
        next_action=status.next_action,
    )


def _format_callbacks(callbacks: tuple[str, ...]) -> str:
    if len(callbacks) == 0:
        return "none"
    return ",".join(callbacks)


def _exit_with_config_error(exc: ConfigLoadError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc


def _exit_with_strategy_error(exc: StrategyContractError) -> NoReturn:
    sys.stderr.write(f"{exc.code.value}: {exc.message}\n")
    raise typer.Exit(code=1) from exc
