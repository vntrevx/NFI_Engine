from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum, unique
from types import MappingProxyType
from typing import Final, assert_never

from nfi_engine.domain import TradingMode

PROOF_SOURCE: Final = "src/nfi_engine/exchange/mode_runtime_proofs.py"


@unique
class RuntimeProofKind(StrEnum):
    SIMULATOR = "simulator"
    TESTNET_ADAPTER = "testnet-adapter"
    TEST_ORDER = "test-order"
    DETERMINISTIC_FIXTURE = "deterministic-fixture"


@unique
class RuntimeProofChannel(StrEnum):
    READ_ONLY_BALANCE = "read_only_balance"
    ORDER_LANE = "order_lane"
    TEST_ENVIRONMENT = "test_environment"


@dataclass(frozen=True, slots=True)
class BalanceProbeFixture:
    asset: str
    wallet_surface: str
    permission: str


@dataclass(frozen=True, slots=True)
class OrderLaneFixture:
    symbol: str
    order_type: str
    safety: str


@dataclass(frozen=True, slots=True)
class ExchangeModeRuntimeProof:
    key: str
    exchange_id: str
    trading_mode: TradingMode
    kind: RuntimeProofKind
    balance: BalanceProbeFixture
    order: OrderLaneFixture


MODE_RUNTIME_PROOFS: Final = MappingProxyType(
    {
        proof.key: proof
        for proof in (
            ExchangeModeRuntimeProof(
                "simulator:spot",
                "simulator",
                TradingMode.SPOT,
                RuntimeProofKind.SIMULATOR,
                BalanceProbeFixture("USDT", "in-memory spot wallet", "none"),
                OrderLaneFixture("BTC/USDT", "limit", "deterministic simulator"),
            ),
            ExchangeModeRuntimeProof(
                "simulator:futures",
                "simulator",
                TradingMode.FUTURES,
                RuntimeProofKind.SIMULATOR,
                BalanceProbeFixture("USDT", "in-memory futures wallet", "none"),
                OrderLaneFixture("BTC/USDT:USDT", "limit", "deterministic simulator"),
            ),
            ExchangeModeRuntimeProof(
                "binance:spot",
                "binance",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "spot account", "USER_DATA"),
                OrderLaneFixture("BTC/USDT", "limit", "dry-run order shape"),
            ),
            ExchangeModeRuntimeProof(
                "binance:futures",
                "binance",
                TradingMode.FUTURES,
                RuntimeProofKind.TEST_ORDER,
                BalanceProbeFixture("USDT", "USD-M futures account", "USER_DATA"),
                OrderLaneFixture("BTC/USDT:USDT", "limit", "futures test-order endpoint"),
            ),
            ExchangeModeRuntimeProof(
                "bingx:spot",
                "bingx",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "spot account", "read-only"),
                OrderLaneFixture("BTC/USDT", "limit", "dry-run order shape"),
            ),
            ExchangeModeRuntimeProof(
                "bitmart:spot",
                "bitmart",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "spot wallet", "Read-Only"),
                OrderLaneFixture("BTC/USDT", "limit", "memo-scoped dry-run order shape"),
            ),
            ExchangeModeRuntimeProof(
                "bitget:spot",
                "bitget",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "spot account", "read-only"),
                OrderLaneFixture("BTC/USDT", "limit", "passphrase-scoped dry-run order shape"),
            ),
            ExchangeModeRuntimeProof(
                "bitget:futures",
                "bitget",
                TradingMode.FUTURES,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "contract account", "read-only"),
                OrderLaneFixture("BTC/USDT:USDT", "limit", "passphrase-scoped dry-run order shape"),
            ),
            ExchangeModeRuntimeProof(
                "bybit:spot",
                "bybit",
                TradingMode.SPOT,
                RuntimeProofKind.TESTNET_ADAPTER,
                BalanceProbeFixture("USDT", "unified spot wallet", "Wallet"),
                OrderLaneFixture("BTC/USDT", "limit", "testnet fake-client order shape"),
            ),
            ExchangeModeRuntimeProof(
                "bybit:futures",
                "bybit",
                TradingMode.FUTURES,
                RuntimeProofKind.TESTNET_ADAPTER,
                BalanceProbeFixture("USDT", "unified futures wallet", "Wallet"),
                OrderLaneFixture("BTC/USDT:USDT", "limit", "testnet fake-client order shape"),
            ),
            ExchangeModeRuntimeProof(
                "gateio:spot",
                "gateio",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "spot wallet", "spot read"),
                OrderLaneFixture("BTC/USDT", "limit", "dry-run order shape"),
            ),
            ExchangeModeRuntimeProof(
                "gateio:futures",
                "gateio",
                TradingMode.FUTURES,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "perpetual account", "perpetual read"),
                OrderLaneFixture("BTC/USDT:USDT", "limit", "futures dry-run order shape"),
            ),
            ExchangeModeRuntimeProof(
                "htx:spot",
                "htx",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "spot account", "read"),
                OrderLaneFixture("BTC/USDT", "limit", "dry-run order shape"),
            ),
            ExchangeModeRuntimeProof(
                "hyperliquid:spot",
                "hyperliquid",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDC", "account address", "account query"),
                OrderLaneFixture("BTC/USDC", "limit", "api-wallet signed dry-run shape"),
            ),
            ExchangeModeRuntimeProof(
                "hyperliquid:futures",
                "hyperliquid",
                TradingMode.FUTURES,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDC", "account address", "account query"),
                OrderLaneFixture("BTC/USDC:USDC", "limit", "api-wallet signed dry-run shape"),
            ),
            ExchangeModeRuntimeProof(
                "kraken:spot",
                "kraken",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USD", "spot balance", "Query Funds"),
                OrderLaneFixture("BTC/USD", "limit", "dry-run order shape"),
            ),
            ExchangeModeRuntimeProof(
                "kraken-futures:futures",
                "kraken-futures",
                TradingMode.FUTURES,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USD", "derivatives account", "derivatives read"),
                OrderLaneFixture("PI_XBTUSD", "limit", "demo-environment order shape"),
            ),
            ExchangeModeRuntimeProof(
                "okx:spot",
                "okx",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "spot account", "Read"),
                OrderLaneFixture("BTC/USDT", "limit", "simulated-trading order shape"),
            ),
            ExchangeModeRuntimeProof(
                "okx:futures",
                "okx",
                TradingMode.FUTURES,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "futures account", "Read"),
                OrderLaneFixture("BTC/USDT:USDT", "limit", "simulated-trading order shape"),
            ),
            ExchangeModeRuntimeProof(
                "bitvavo:spot",
                "bitvavo",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("EUR", "spot balance", "View"),
                OrderLaneFixture("BTC/EUR", "limit", "operator-id dry-run order shape"),
            ),
            ExchangeModeRuntimeProof(
                "kucoin:spot",
                "kucoin",
                TradingMode.SPOT,
                RuntimeProofKind.DETERMINISTIC_FIXTURE,
                BalanceProbeFixture("USDT", "spot account", "General"),
                OrderLaneFixture("BTC/USDT", "limit", "passphrase-scoped order-test shape"),
            ),
        )
    },
)


def all_runtime_proof_keys() -> tuple[str, ...]:
    return tuple(MODE_RUNTIME_PROOFS)


def runtime_proof_evidence(key: str, channel: RuntimeProofChannel) -> str:
    proof = MODE_RUNTIME_PROOFS[key]
    match channel:
        case RuntimeProofChannel.READ_ONLY_BALANCE:
            label = f"{proof.key}:balance:{proof.balance.asset}"
        case RuntimeProofChannel.ORDER_LANE:
            label = f"{proof.key}:order:{proof.order.symbol}"
        case RuntimeProofChannel.TEST_ENVIRONMENT:
            label = f"{proof.key}:environment:{proof.kind.value}"
        case unreachable:
            assert_never(unreachable)
    return f"{PROOF_SOURCE}#{label}"
