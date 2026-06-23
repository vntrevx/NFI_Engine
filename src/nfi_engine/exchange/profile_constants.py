from __future__ import annotations

from datetime import date
from typing import Final

from nfi_engine.domain import MarginMode, OrderType

CHECKED_ON: Final = date(2026, 6, 14)
DOC_EVIDENCE: Final = "docs/exchange-support-matrix.md"
SIMULATOR_EVIDENCE: Final = "tests/unit/exchange/test_simulator.py"
BYBIT_TESTNET_CHECKED_ON: Final = date(2026, 6, 21)
BYBIT_TESTNET_EVIDENCE: Final = "tests/integration/exchange/test_bybit_adapter.py"
KEY_SECRET: Final = ("api_key", "api_secret")
KEY_SECRET_PASS: Final = ("api_key", "api_secret", "passphrase")
MARKET_LIMIT: Final = (OrderType.MARKET, OrderType.LIMIT)
ISOLATED: Final = (MarginMode.ISOLATED,)
ISOLATED_CROSS: Final = (MarginMode.ISOLATED, MarginMode.CROSS)
