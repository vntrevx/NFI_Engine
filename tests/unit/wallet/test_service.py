from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal

import anyio
import pytest

from nfi_engine.config.models import RuntimeSettings
from nfi_engine.domain import AccountSnapshot, StakeAmount
from nfi_engine.exchange.errors import ExchangeError, ExchangeErrorCode
from nfi_engine.exchange.permissions import ExchangeApiPermissionState
from nfi_engine.wallet import WalletBalanceCode, WalletBalanceStatus, fetch_wallet_balance

pytestmark = pytest.mark.anyio
NOW = datetime(2026, 6, 15, tzinfo=UTC)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


async def test_simulator_wallet_balance_fetches_through_exchange_boundary() -> None:
    # Given: the default simulator profile used for local paper operation.
    settings = RuntimeSettings()

    # When: wallet balance is requested from the service boundary.
    balance = await fetch_wallet_balance(settings=settings, now=NOW)

    # Then: the deterministic simulator account is returned without credentials.
    assert balance.status is WalletBalanceStatus.FETCHED
    assert balance.code is WalletBalanceCode.FETCHED
    assert balance.captured_at == NOW
    assert balance.equity == Decimal(1000)
    assert balance.available == Decimal(1000)
    assert balance.quote_asset == "USDT"
    assert balance.allocation_cap_pct == Decimal("0.10")
    assert balance.allocation_cap == Decimal("100.00")
    assert balance.configured_allocation_total == Decimal(30)
    assert balance.allocation_cap_exceeded is False
    assert balance.permission_audit.withdrawal is ExchangeApiPermissionState.UNKNOWN


async def test_wallet_balance_blocks_non_simulator_without_credentials() -> None:
    # Given: a testnet exchange config with no API key or secret.
    settings = RuntimeSettings.model_validate({"exchange": {"name": "bybit", "testnet": True}})

    # When: the operator asks for wallet balance.
    balance = await fetch_wallet_balance(settings=settings)

    # Then: the response is machine-coded and contains no secret material.
    assert balance.status is WalletBalanceStatus.BLOCKED
    assert balance.code is WalletBalanceCode.MISSING_CREDENTIALS
    assert balance.equity is None
    assert balance.available is None
    assert "secret" not in balance.message.lower()
    assert "api_key" in balance.next_action
    assert "api_secret" in balance.next_action


async def test_wallet_balance_names_exchange_specific_missing_credentials() -> None:
    # Given: Bitget has key and secret configured, but its official passphrase is missing.
    settings = RuntimeSettings.model_validate(
        {
            "exchange": {
                "name": "bitget",
                "testnet": True,
                "api_key": "redacted-test-key",
                "api_secret": "redacted-test-secret",
            },
        },
    )

    # When: the operator asks for wallet balance.
    balance = await fetch_wallet_balance(settings=settings)

    # Then: the blocker names the exchange-specific missing field without echoing secrets.
    assert balance.status is WalletBalanceStatus.BLOCKED
    assert balance.code is WalletBalanceCode.MISSING_CREDENTIALS
    assert "passphrase" in balance.next_action
    assert "api_key" not in balance.next_action
    assert "api_secret" not in balance.next_action
    assert "redacted-test-key" not in balance.next_action
    assert "redacted-test-secret" not in balance.next_action


async def test_wallet_balance_blocks_live_intent_with_withdrawal_permission() -> None:
    # Given: live intent with an unsafe exchange API permission state.
    settings = RuntimeSettings.model_validate(
        {
            "engine": {"live_trading": True, "live_trading_confirmed": True},
            "exchange": {
                "name": "bybit",
                "testnet": True,
                "api_key": "redacted-test-key",
                "api_secret": "redacted-test-secret",
                "permission_withdrawal": "enabled",
            },
        },
    )

    # When: wallet balance is requested.
    balance = await fetch_wallet_balance(settings=settings, reader=FakeBalanceReader())

    # Then: read inspection is blocked until withdrawal permission is removed.
    assert balance.status is WalletBalanceStatus.BLOCKED
    assert balance.code is WalletBalanceCode.UNSAFE_PERMISSION
    assert balance.permission_audit.withdrawal is ExchangeApiPermissionState.ENABLED
    assert balance.permission_audit.live_safe is False
    assert balance.permission_audit.live_blocking_codes == (
        "EXCHANGE_WITHDRAWAL_PERMISSION_ENABLED",
    )
    assert "redacted-test-key" not in balance.next_action
    assert "redacted-test-secret" not in balance.next_action


async def test_wallet_balance_uses_injected_read_only_adapter() -> None:
    # Given: a configured exchange and an injected read-only balance adapter.
    settings = RuntimeSettings.model_validate(
        {
            "exchange": {
                "name": "bybit",
                "testnet": True,
                "api_key": "redacted-test-key",
                "api_secret": "redacted-test-secret",
            },
        },
    )

    # When: wallet balance is fetched.
    balance = await fetch_wallet_balance(settings=settings, reader=FakeBalanceReader())

    # Then: the adapter result is normalized to the public wallet snapshot.
    assert balance.status is WalletBalanceStatus.FETCHED
    assert balance.equity == Decimal("77.5")
    assert balance.available == Decimal(70)
    assert balance.position_count == 0
    assert balance.allocation_cap == Decimal("7.00")
    assert balance.configured_allocation_total == Decimal(30)
    assert balance.allocation_cap_exceeded is True


async def test_wallet_balance_returns_machine_code_for_exchange_error() -> None:
    # Given: an injected reader that reports an exchange failure.
    settings = RuntimeSettings()

    # When: wallet balance is fetched.
    balance = await fetch_wallet_balance(settings=settings, reader=FailingBalanceReader())

    # Then: the failure is redacted and machine-coded.
    assert balance.status is WalletBalanceStatus.ERROR
    assert balance.code is WalletBalanceCode.EXCHANGE_ERROR
    assert balance.message == ExchangeErrorCode.TICK_NOT_FOUND.value


async def test_wallet_balance_returns_timeout_code_when_reader_is_slow() -> None:
    # Given: an injected reader slower than the wallet timeout budget.
    settings = RuntimeSettings()

    # When: wallet balance fetch exceeds the configured timeout.
    balance = await fetch_wallet_balance(
        settings=settings,
        reader=SlowBalanceReader(),
        timeout_seconds=0.01,
    )

    # Then: the operator gets a stable timeout diagnostic instead of a hung request.
    assert balance.status is WalletBalanceStatus.ERROR
    assert balance.code is WalletBalanceCode.TIMEOUT
    assert balance.allocation_cap is None
    assert balance.allocation_cap_exceeded is None


@dataclass(frozen=True, slots=True)
class FakeBalanceReader:
    async def fetch_balance(self) -> AccountSnapshot:
        return AccountSnapshot(
            captured_at=NOW,
            equity=StakeAmount(Decimal("77.5")),
            available=StakeAmount(Decimal(70)),
            positions=(),
        )


@dataclass(frozen=True, slots=True)
class FailingBalanceReader:
    async def fetch_balance(self) -> AccountSnapshot:
        raise ExchangeError(
            code=ExchangeErrorCode.TICK_NOT_FOUND,
            message="synthetic reader failure",
        )


@dataclass(frozen=True, slots=True)
class SlowBalanceReader:
    async def fetch_balance(self) -> AccountSnapshot:
        await anyio.sleep(1)
        return AccountSnapshot(
            captured_at=NOW,
            equity=StakeAmount(Decimal(1)),
            available=StakeAmount(Decimal(1)),
            positions=(),
        )
