from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from types import MappingProxyType
from typing import Final, Protocol

import anyio

from nfi_engine.config import RuntimeSettings
from nfi_engine.domain import AccountSnapshot, DomainError, Price, TradingMode, TradingPair
from nfi_engine.exchange import get_exchange_profile
from nfi_engine.exchange.binance import BinanceFuturesBalanceAdapter
from nfi_engine.exchange.credential_requirements import missing_runtime_credential_fields
from nfi_engine.exchange.errors import ExchangeError
from nfi_engine.exchange.models import Tick
from nfi_engine.exchange.simulator import DeterministicExchangeSimulator
from nfi_engine.wallet.models import (
    WalletBalanceCode,
    WalletBalanceSnapshot,
    WalletBalanceStatus,
    WalletPermissionAuditSnapshot,
)

DEFAULT_TIMEOUT_SECONDS: Final = 2.0


class WalletBalanceReader(Protocol):
    async def fetch_balance(self) -> AccountSnapshot: ...


class WalletBalanceReaderFactory(Protocol):
    def __call__(
        self,
        settings: RuntimeSettings,
        now: datetime | None,
    ) -> WalletBalanceReader | None: ...


async def fetch_wallet_balance(
    *,
    settings: RuntimeSettings,
    reader: WalletBalanceReader | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    now: datetime | None = None,
) -> WalletBalanceSnapshot:
    blocked = _blocked_diagnostic(settings)
    if blocked is not None:
        return blocked

    balance_reader = reader
    if balance_reader is None:
        balance_reader = _default_reader(settings=settings, now=now)
    if balance_reader is None:
        return WalletBalanceSnapshot.diagnostic(
            settings=settings,
            status=WalletBalanceStatus.UNAVAILABLE,
            code=WalletBalanceCode.ADAPTER_UNAVAILABLE,
            next_action="Install or inject a read-only exchange adapter before fetching balance.",
            message="No wallet balance adapter is available for this exchange profile.",
        )

    account: AccountSnapshot | None = None
    try:
        with anyio.move_on_after(timeout_seconds) as cancel_scope:
            account = await balance_reader.fetch_balance()
    except ExchangeError as exc:
        return WalletBalanceSnapshot.diagnostic(
            settings=settings,
            status=WalletBalanceStatus.ERROR,
            code=WalletBalanceCode.EXCHANGE_ERROR,
            next_action="Open Logs and inspect the exchange adapter diagnostic code.",
            message=exc.code.value,
        )
    if cancel_scope.cancel_called or account is None:
        return WalletBalanceSnapshot.diagnostic(
            settings=settings,
            status=WalletBalanceStatus.ERROR,
            code=WalletBalanceCode.TIMEOUT,
            next_action="Retry after checking exchange latency or reduce adapter timeout.",
            message="Wallet balance fetch timed out.",
        )
    return WalletBalanceSnapshot.from_account(settings=settings, account=account)


def _blocked_diagnostic(settings: RuntimeSettings) -> WalletBalanceSnapshot | None:
    audit = WalletPermissionAuditSnapshot.from_settings(settings)
    if settings.engine.live_trading and not audit.live_safe:
        return WalletBalanceSnapshot.diagnostic(
            settings=settings,
            status=WalletBalanceStatus.BLOCKED,
            code=WalletBalanceCode.UNSAFE_PERMISSION,
            next_action="Disable withdrawal permission before any live-intent wallet check.",
            message="Exchange API permissions are not safe for live-intent operation.",
        )
    missing_credentials = _missing_credentials(settings)
    if _requires_credentials(settings) and missing_credentials:
        return WalletBalanceSnapshot.diagnostic(
            settings=settings,
            status=WalletBalanceStatus.BLOCKED,
            code=WalletBalanceCode.MISSING_CREDENTIALS,
            next_action=(
                "Add read-only exchange credentials in Settings setup: "
                f"{', '.join(missing_credentials)}."
            ),
            message="Wallet balance fetch needs exchange credentials.",
        )
    return None


def _default_reader(
    *,
    settings: RuntimeSettings,
    now: datetime | None,
) -> WalletBalanceReader | None:
    profile = get_exchange_profile(settings.exchange.name)
    if profile is None:
        return None
    factory = WALLET_READER_FACTORIES.get(profile.exchange_id)
    if factory is None:
        return None
    return factory(settings, now)


def _simulator_reader(settings: RuntimeSettings, now: datetime | None) -> WalletBalanceReader:
    at = now if now is not None else datetime.now(UTC)
    return DeterministicExchangeSimulator(
        ticks=(
            Tick(
                pair=_first_pair(settings),
                price=Price(Decimal(1)),
                at=at,
            ),
        ),
    )


def _binance_reader(
    settings: RuntimeSettings,
    now: datetime | None,
) -> WalletBalanceReader | None:
    del now
    match settings.exchange.trading_mode:
        case TradingMode.FUTURES:
            return BinanceFuturesBalanceAdapter.from_settings(settings=settings)
        case TradingMode.SPOT:
            return None


WALLET_READER_FACTORIES: Final[Mapping[str, WalletBalanceReaderFactory]] = MappingProxyType(
    {
        "simulator": _simulator_reader,
        "binance": _binance_reader,
    },
)


def _first_pair(settings: RuntimeSettings) -> TradingPair:
    for raw_pair in settings.pairlist.whitelist.split(","):
        pair_text = raw_pair.strip()
        if pair_text == "":
            continue
        try:
            return TradingPair.parse(pair_text, settings.exchange.trading_mode)
        except DomainError:
            continue
    fallback = "BTC/USDT:USDT" if settings.exchange.trading_mode.value == "futures" else "BTC/USDT"
    return TradingPair.parse(fallback, settings.exchange.trading_mode)


def _requires_credentials(settings: RuntimeSettings) -> bool:
    profile = get_exchange_profile(settings.exchange.name)
    if profile is None:
        return True
    return bool(profile.credential_fields)


def _missing_credentials(settings: RuntimeSettings) -> tuple[str, ...]:
    return missing_runtime_credential_fields(settings)
