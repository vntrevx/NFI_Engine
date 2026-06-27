from __future__ import annotations

from nfi_engine.config.models import RuntimeSettings
from nfi_engine.domain import TradingMode
from nfi_engine.exchange.capability_models import ExchangeCapabilityProfile
from nfi_engine.exchange.runtime_verification_check_builders import (
    block_check,
    manual_check,
    pass_check,
)
from nfi_engine.exchange.runtime_verification_evidence import DRY_RUN_ENVIRONMENT_EVIDENCE
from nfi_engine.exchange.runtime_verification_models import ExchangeRuntimeCheck


def test_environment_check(
    *,
    settings: RuntimeSettings | None,
    profile: ExchangeCapabilityProfile,
    trading_mode: TradingMode,
) -> ExchangeRuntimeCheck:
    if profile.exchange_id == "simulator":
        return pass_check(
            stage="test_environment",
            code="TEST_ENVIRONMENT_SIMULATOR",
            message="Simulator is deterministic and does not need exchange testnet access.",
        )
    if settings is None:
        return manual_check(
            stage="test_environment",
            code="TEST_ENVIRONMENT_NOT_LOADED",
            message="Runtime config was not loaded for testnet/sandbox validation.",
            next_action="Run runtime-check with --config before promotion.",
        )
    return _loaded_test_environment_check(
        settings=settings,
        profile=profile,
        trading_mode=trading_mode,
    )


def _loaded_test_environment_check(
    *,
    settings: RuntimeSettings,
    profile: ExchangeCapabilityProfile,
    trading_mode: TradingMode,
) -> ExchangeRuntimeCheck:
    if settings.engine.live_trading:
        return block_check(
            stage="test_environment",
            code="LIVE_RUNTIME_DISABLED_FOR_PROMOTION",
            message="Live trading cannot be used as a promotion proof in this milestone.",
            next_action="Use paper/testnet/sandbox proof before any live promotion.",
        )
    if not settings.exchange.testnet:
        return block_check(
            stage="test_environment",
            code="TESTNET_REQUIRED_FOR_PROMOTION",
            message="Runtime verification requires testnet=true outside the simulator.",
            next_action="Enable testnet or provide a sandbox-backed config.",
        )
    if profile.supports_testnet or profile.supports_sandbox:
        return pass_check(
            stage="test_environment",
            code="TEST_ENVIRONMENT_SUPPORTED",
            message="Registry profile supports testnet or sandbox verification.",
        )
    evidence = DRY_RUN_ENVIRONMENT_EVIDENCE.get(
        f"{profile.exchange_id}:{trading_mode.value}",
    )
    if evidence is not None:
        return pass_check(
            stage="test_environment",
            code="DETERMINISTIC_DRY_RUN_EVIDENCE_PRESENT",
            message=f"Deterministic dry-run evidence exists at {evidence}.",
        )
    return block_check(
        stage="test_environment",
        code="TEST_ENVIRONMENT_UNAVAILABLE",
        message="Registry profile has no confirmed testnet, sandbox, or dry-run evidence lane.",
        next_action="Add exchange-specific safe verification evidence before promotion.",
    )
