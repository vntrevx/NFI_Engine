from __future__ import annotations

from nfi_engine.sandbox import SandboxViolationKind, check_strategy_sandbox


def test_nfi_strategy_passes_with_approved_capabilities() -> None:
    # Given
    strategy = "tests.fixtures.strategies.nfi_shape:NFISmokeStrategy"

    # When
    result = check_strategy_sandbox(strategy)

    # Then
    assert result.passed is True
    assert "data_provider" in result.approved_capabilities
    assert "callback_context" in result.approved_capabilities
    assert result.violations == ()


def test_environment_read_is_blocked_before_strategy_import() -> None:
    # Given
    strategy = "tests.fixtures.strategies.unsafe:EnvReadingStrategy"

    # When
    result = check_strategy_sandbox(strategy)

    # Then
    assert result.passed is False
    assert result.violations[0].kind is SandboxViolationKind.ENV_READ


def test_filesystem_write_is_blocked() -> None:
    # Given
    strategy = "tests.fixtures.strategies.unsafe:FilesystemWritingStrategy"

    # When
    result = check_strategy_sandbox(strategy)

    # Then
    assert result.passed is False
    assert result.violations[0].kind is SandboxViolationKind.FILESYSTEM_WRITE


def test_subprocess_call_is_blocked() -> None:
    # Given
    strategy = "tests.fixtures.strategies.unsafe:SubprocessStrategy"

    # When
    result = check_strategy_sandbox(strategy)

    # Then
    assert result.passed is False
    assert result.violations[0].kind is SandboxViolationKind.SUBPROCESS


def test_direct_network_call_is_blocked() -> None:
    # Given
    strategy = "tests.fixtures.strategies.unsafe:NetworkStrategy"

    # When
    result = check_strategy_sandbox(strategy)

    # Then
    assert result.passed is False
    assert result.violations[0].kind is SandboxViolationKind.NETWORK


def test_direct_exchange_access_is_blocked() -> None:
    # Given
    strategy = "tests.fixtures.strategies.unsafe:DirectExchangeStrategy"

    # When
    result = check_strategy_sandbox(strategy)

    # Then
    assert result.passed is False
    assert result.violations[0].kind is SandboxViolationKind.DIRECT_EXCHANGE_ACCESS
