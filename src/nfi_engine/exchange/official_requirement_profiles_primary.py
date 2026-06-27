from __future__ import annotations

from typing import Final

from nfi_engine.exchange.official_requirement_models import ExchangeOfficialRequirement

PRIMARY_OFFICIAL_REQUIREMENTS: Final = (
    ExchangeOfficialRequirement(
        exchange_id="binance",
        official_doc_url=(
            "https://developers.binance.com/docs/derivatives/usds-margined-futures/general-info"
        ),
        credential_fields=("api_key", "api_secret"),
        secret_fields=("api_secret",),
        identifier_fields=("api_key",),
        required_permissions=(
            "USER_DATA for balance and account reads",
            "TRADE for order placement; withdrawal permissions must stay disabled",
        ),
        account_notes=(
            "Spot and USD-M Futures use separate endpoint families.",
            "USD-M Futures testnet REST uses the demo-fapi endpoint family.",
            "Order eligibility is gated by account and symbol permission sets.",
        ),
        testnet_notes=("Spot testnet/demo and USD-M Futures testnet exist with separate keys.",),
        order_notes=(
            "USD-M Futures test-order requests prove signed order shape without live matching.",
            "Futures stop-loss, take-profit, and trailing stops use conditional order paths.",
        ),
    ),
    ExchangeOfficialRequirement(
        exchange_id="bingx",
        official_doc_url="https://bingx-api.github.io/docs/",
        credential_fields=("api_key", "api_secret"),
        secret_fields=("api_secret",),
        identifier_fields=("api_key",),
        required_permissions=(
            "Read-only for account inspection",
            "Trade for order placement; transfer and withdrawal-like scopes stay disabled",
        ),
        account_notes=(
            "Use the V2 open-api.bingx.com surface for current integrations.",
            "Exact balance and order routes still need adapter-level proof.",
        ),
        testnet_notes=("BingX demo trading uses VST and is not a generic public sandbox.",),
        order_notes=(
            "Demo material covers limit, stop, and OCO practice; endpoint parity needs proof.",
        ),
    ),
    ExchangeOfficialRequirement(
        exchange_id="bitmart",
        official_doc_url="https://developer-pro.bitmart.com/en/spot/",
        credential_fields=("api_key", "api_secret", "memo"),
        secret_fields=("api_secret", "memo"),
        identifier_fields=("api_key",),
        required_permissions=(
            "Read-Only is the default new-key permission",
            "Spot-Trade and Future-Trade are separate explicit permissions",
            "Withdraw must stay disabled",
        ),
        account_notes=(
            "Spot and futures wallet/account routes are separate.",
            "Sub-account futures access requires master-account enablement.",
        ),
        testnet_notes=("No spot API test environment; futures demo uses a separate demo host.",),
        order_notes=(
            "Spot market buys use notional; spot market sells use size.",
            "Futures supports TP/SL plan order paths.",
        ),
    ),
    ExchangeOfficialRequirement(
        exchange_id="bitget",
        official_doc_url="https://www.bitget.com/api-doc/common/quick-start",
        credential_fields=("api_key", "api_secret", "passphrase"),
        secret_fields=("api_secret", "passphrase"),
        identifier_fields=("api_key",),
        required_permissions=(
            "Read-only for inspection",
            "Read/write for trading; withdrawal-like permissions stay disabled",
        ),
        account_notes=(
            "Spot and contract product families expose separate account/order routes.",
            "Classic contract product types include USDT, USDC, and coin-margined futures.",
        ),
        testnet_notes=("Demo trading requires a dedicated demo API key and paptrading header.",),
        order_notes=("Spot plan orders and futures TPSL plan orders are separate order lanes.",),
    ),
    ExchangeOfficialRequirement(
        exchange_id="bybit",
        official_doc_url="https://bybit-exchange.github.io/docs/v5/guide",
        credential_fields=("api_key", "api_secret"),
        secret_fields=("api_secret",),
        identifier_fields=("api_key",),
        required_permissions=(
            "Read-only for account inspection",
            "ContractTrade, Spot, Wallet, and Derivatives permissions are product-scoped",
        ),
        account_notes=(
            "Unified and classic account behavior must be adapter-verified per endpoint.",
        ),
        testnet_notes=("Testnet API keys and Demo Trading accounts are separate from production.",),
        order_notes=(
            "triggerPrice creates conditional orders; TP/SL can be attached at placement.",
        ),
    ),
    ExchangeOfficialRequirement(
        exchange_id="gateio",
        official_doc_url="https://www.gate.io/docs/developers/apiv4/",
        credential_fields=("api_key", "api_secret"),
        secret_fields=("api_secret",),
        identifier_fields=("api_key",),
        required_permissions=(
            "spot/margin, perpetual, delivery, wallet, and withdrawal scopes are separate",
            "Use read-only for inspection and read-write only for the active trade product",
        ),
        account_notes=(
            "APIv4 can share one key across spot and futures with product permissions.",
        ),
        testnet_notes=("Futures testnet uses separate keys; production keys do not work there.",),
        order_notes=("Spot and futures price-trigger order lanes are separate.",),
    ),
    ExchangeOfficialRequirement(
        exchange_id="htx",
        official_doc_url="https://huobiapi.github.io/docs/spot/v1/en/",
        credential_fields=("api_key", "api_secret"),
        secret_fields=("api_secret",),
        identifier_fields=("api_key",),
        required_permissions=(
            "read for inspection",
            "trade for orders; withdraw stays disabled",
        ),
        account_notes=(
            "Spot and futures use the same API key family in official docs.",
            "Private endpoints require signed requests.",
        ),
        testnet_notes=("Official spot docs state that the test environment has stopped.",),
        order_notes=(
            "Spot order history is time-window constrained; client order ids are recommended.",
        ),
    ),
)
