from __future__ import annotations

from typing import Final

from nfi_engine.exchange.official_requirement_models import ExchangeOfficialRequirement

SECONDARY_OFFICIAL_REQUIREMENTS: Final = (
    ExchangeOfficialRequirement(
        exchange_id="hyperliquid",
        official_doc_url=(
            "https://hyperliquid.gitbook.io/hyperliquid-docs/"
            "for-developers/api/nonces-and-api-wallets"
        ),
        credential_fields=("account_address", "api_wallet_signer"),
        secret_fields=("api_wallet_signer",),
        identifier_fields=("account_address",),
        required_permissions=(
            "Use an approved API wallet signer; never use the main wallet seed path",
            "Account-data queries must target the real account or sub-account address",
        ),
        account_notes=(
            "Agent/API wallets sign actions but are not the account address queried for data.",
            "Nonce handling is signer-scoped and must not be shared across bot processes.",
        ),
        testnet_notes=("Testnet exists, but faucet access has account-history requirements.",),
        order_notes=(
            "Spot and perpetual books exist; market behavior and TP/SL need signer proof.",
        ),
    ),
    ExchangeOfficialRequirement(
        exchange_id="kraken",
        official_doc_url="https://docs.kraken.com/exchange/guides/rest/api-keys",
        credential_fields=("api_key", "api_secret"),
        secret_fields=("api_secret",),
        identifier_fields=("api_key",),
        required_permissions=(
            "Query Funds for balances",
            "Query orders/trades for history",
            "Create/Modify Orders and Cancel/Close Orders for trading",
        ),
        account_notes=(
            "Spot and Futures are separate engine surfaces.",
            "Private WebSocket streams require a short-lived WebSocket token.",
        ),
        testnet_notes=("Spot UAT exists only by request with isolated keys.",),
        order_notes=(
            "Kraken historic candle depth is limited; backtests may require trade downloads.",
        ),
    ),
    ExchangeOfficialRequirement(
        exchange_id="kraken-futures",
        official_doc_url="https://docs.kraken.com/exchange/guides/futures/rest",
        credential_fields=("api_key", "api_secret"),
        secret_fields=("api_secret",),
        identifier_fields=("api_key",),
        required_permissions=(
            "Use derivative API credentials separate from Kraken Spot credentials",
        ),
        account_notes=(
            "Futures exposes balance, PnL, margin, position, and order-history routes.",
        ),
        testnet_notes=("Self-service demo futures environment uses separate demo API keys.",),
        order_notes=("Futures supports market, limit, stop, take-profit, IOC, and batch orders.",),
    ),
    ExchangeOfficialRequirement(
        exchange_id="okx",
        official_doc_url="https://www.okx.com/docs-v5/en/",
        credential_fields=("api_key", "api_secret", "passphrase"),
        secret_fields=("api_secret", "passphrase"),
        identifier_fields=("api_key",),
        required_permissions=(
            "Read for balances and account state",
            "Trade for order placement; withdraw stays disabled",
            "Live order placement can require KYC Level 2 or above",
        ),
        account_notes=(
            "Sub-account keys with trade or withdraw permissions can require IP binding.",
            "Spot, swap, and futures-style instruments share the v5 API family.",
        ),
        testnet_notes=("Demo trading uses the simulated-trading flag/header path.",),
        order_notes=("Regular orders and algo/conditional orders are separate endpoints.",),
    ),
    ExchangeOfficialRequirement(
        exchange_id="bitvavo",
        official_doc_url="https://docs.bitvavo.com/docs/rest-api/introduction/",
        credential_fields=("api_key", "api_secret", "operator_id"),
        secret_fields=("api_secret",),
        identifier_fields=("api_key", "operator_id"),
        required_permissions=(
            "View access for balances and history",
            "Trade digital assets for order changes",
            "Withdraw digital assets must stay disabled",
        ),
        account_notes=(
            "Official docs describe spot/digital-asset trading, not futures/perpetuals.",
        ),
        testnet_notes=("No official public sandbox was confirmed in the checked docs.",),
        order_notes=(
            "operatorId is required on create, update, and cancel order requests.",
            "Supported order types include market, limit, stopLoss, and takeProfit variants.",
        ),
    ),
    ExchangeOfficialRequirement(
        exchange_id="kucoin",
        official_doc_url="https://www.kucoin.com/docs-new/authentication",
        credential_fields=("api_key", "api_secret", "passphrase"),
        secret_fields=("api_secret", "passphrase"),
        identifier_fields=("api_key",),
        required_permissions=(
            "General, Spot, Margin, Futures, Earn, Withdrawal, and transfer permissions differ",
            "Withdrawal and transfer-like permissions must stay disabled for NFI Engine",
        ),
        account_notes=("Spot and Futures account/order surfaces are separate permission groups.",),
        testnet_notes=("No public sandbox/testnet was confirmed in the checked official pages.",),
        order_notes=(
            "Spot has a non-matching order-test endpoint; futures TP/SL has dedicated routes.",
        ),
    ),
)
