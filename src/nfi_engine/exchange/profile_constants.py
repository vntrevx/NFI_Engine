from __future__ import annotations

from datetime import date
from typing import Final

from nfi_engine.domain import MarginMode, OrderType

CHECKED_ON: Final = date(2026, 6, 14)
DOC_EVIDENCE: Final = "docs/exchange-support-matrix.md"
SIMULATOR_EVIDENCE: Final = "tests/unit/exchange/test_simulator.py"
BATCH_RUNTIME_CHECKED_ON: Final = date(2026, 6, 26)
BATCH_RUNTIME_EVIDENCE: Final = "src/nfi_engine/exchange/mode_runtime_proofs.py"
BYBIT_TESTNET_CHECKED_ON: Final = date(2026, 6, 21)
BYBIT_TESTNET_EVIDENCE: Final = "tests/integration/exchange/test_bybit_adapter.py"
BINANCE_FUTURES_CHECKED_ON: Final = date(2026, 6, 25)
BINANCE_FUTURES_EVIDENCE: Final = "tests/integration/exchange/test_binance_order_test_adapter.py"
KEY_SECRET: Final = ("api_key", "api_secret")
KEY_SECRET_MEMO: Final = ("api_key", "api_secret", "memo")
KEY_SECRET_OPERATOR: Final = ("api_key", "api_secret", "operator_id")
KEY_SECRET_PASS: Final = ("api_key", "api_secret", "passphrase")
ACCOUNT_SIGNER: Final = ("account_address", "api_wallet_signer")
MARKET_LIMIT: Final = (OrderType.MARKET, OrderType.LIMIT)
ISOLATED: Final = (MarginMode.ISOLATED,)
ISOLATED_CROSS: Final = (MarginMode.ISOLATED, MarginMode.CROSS)
