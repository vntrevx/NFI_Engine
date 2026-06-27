# Exchange Support Matrix

This matrix converts exchange coverage into NFI Engine capability levels.
Runtime verification here means NFI Engine has a checked-in mode-scoped
deterministic fixture, credential, balance-read, and dry-run/order-lane
evidence path. It is not a live-money readiness claim.

Freqtrade baseline checked on 2026-06-14. Exchange official docs rechecked on
2026-06-25. Bybit local testnet adapter evidence checked on 2026-06-21:
`https://www.freqtrade.io/en/stable/exchanges/`.
Binance USD-M Futures local signed balance and test-order evidence checked on
2026-06-25. All registered exchange/mode fixture-proof evidence checked on
2026-06-26.

## Verification levels

| Level | Meaning | Live-mode rule |
| --- | --- | --- |
| `verified` | NFI Engine has exact exchange evidence from a checked-in deterministic fixture, simulator, testnet, or sandbox lane. | Live can only proceed through normal live gates after preflight, credential audit, balance cap, circuit breaker, and reconciliation checks. |
| `candidate` | The exchange is known, but NFI Engine has not promoted it with local deterministic evidence. | Dry-run/paper research only; live remains blocked until promoted. |
| `generic-unverified` | A broader CCXT-style or custom exchange id can be configured/probed later, but is not first-class. | Live blocked; capability discovery may produce a report, not a trade path. |

Promotion rule: never promote an exchange from `candidate` or
`generic-unverified` to `verified` from a docs table alone. Promotion requires
a named artifact under `.omo/evidence/` or a checked-in deterministic fixture.

## Runtime promotion check

As of 2026-06-26, `nfi-engine exchange runtime-check` gives each registered
exchange mode the same promotion checklist before it can be considered
config-backed promotion-ready:

- explicit registry profile.
- official requirement profile.
- supported trading mode.
- config-backed credential readiness.
- paper/testnet/sandbox or deterministic dry-run environment readiness.
- read-only balance evidence.
- dry-run or testnet order-lane evidence.

Examples:

```bash
uv run nfi-engine exchange runtime-check --all --format json
uv run nfi-engine exchange runtime-check --exchange bitvavo --trading-mode spot
uv run nfi-engine exchange runtime-check --config examples/futures-paper.yaml
```

The command is intentionally strict. A report-only `--all` run does not load
operator config, so it can show `runtime_verified=true` while leaving
`promotion_ready=false` for credentials or environment checks. A config-backed
run with fixture credentials, `testnet=true`, and `live_trading=false` must
close every registered mode without evidence blockers. Missing
exchange-specific fields still return machine-readable blockers, for example
Bitvavo `operator_id`, Bitget `passphrase`, or Hyperliquid
`api_wallet_signer`. `live_trading=true` is never accepted as promotion proof.

Binance Futures keeps its stronger signed USD-M Futures balance and
`/fapi/v1/order/test` proof. The other registered modes are verified by the
mode-scoped deterministic fixture ledger in
`src/nfi_engine/exchange/mode_runtime_proofs.py`. They still need
separate live-operator proof before any public live-money readiness claim.

## Official requirement profile

NFI Engine now keeps official exchange-document requirements separately from the
runtime verification level in `src/nfi_engine/exchange/official_requirements.py`.
This table is used by the CLI and Settings UI to explain what each venue needs.
It does not mean the venue is live-ready or promoted to `verified`.

| Exchange | Official setup fields | Permission baseline | Non-production note |
| --- | --- | --- | --- |
| Binance | `api_key`, `api_secret` | `USER_DATA` for account reads, `TRADE` only for order placement, withdrawals disabled | Spot testnet/demo and USD-M Futures testnet use separate keys |
| BingX | `api_key`, `api_secret` | read-only for inspection, trade only for order placement, transfer-like scopes disabled | VST demo trading exists for perpetual futures; exact endpoint parity still needs adapter proof |
| BitMart | `api_key`, `api_secret`, `memo` | new keys default to read-only; spot/futures trade permissions are separate; withdrawals disabled | no spot API test environment was confirmed; futures demo uses a separate host |
| Bitget | `api_key`, `api_secret`, `passphrase` | read-only for inspection, read/write only for active trading, withdrawal-like permissions disabled | demo trading needs a demo key and `paptrading` request header |
| Bybit | `api_key`, `api_secret` | product-scoped permissions such as ContractTrade, Spot, Wallet, and Derivatives | testnet keys and Demo Trading accounts are separate from production |
| Gate.io | `api_key`, `api_secret` | product scopes cover spot/margin, perpetual, delivery, wallet, and withdrawal; enable only the required trade product | futures testnet uses separate keys |
| HTX | `api_key`, `api_secret` | read for inspection, trade for order placement, withdraw disabled | spot docs state the test environment has stopped |
| Hyperliquid | `account_address`, `api_wallet_signer` | approved API wallet signer plus real account/sub-account address; never use wallet seed paths | testnet exists, but faucet/account prerequisites apply |
| Kraken | `api_key`, `api_secret` | Query Funds, query orders/trades, create/modify orders, cancel/close orders | spot UAT exists by request with isolated keys |
| Kraken Futures | `api_key`, `api_secret` | derivative API credentials are separate from Kraken Spot credentials | self-service demo futures uses separate demo API keys |
| OKX | `api_key`, `api_secret`, `passphrase` | Read for account state, Trade for orders, withdrawals disabled; live orders can require KYC Level 2+ | demo trading uses the simulated-trading flag/header path |
| Bitvavo | `api_key`, `api_secret`, `operator_id` | View access for balances/history, Trade digital assets for orders, withdrawals disabled | no public sandbox was confirmed in checked docs |
| KuCoin | `api_key`, `api_secret`, `passphrase` | General, Spot, Margin, Futures, Earn, Withdrawal, and transfer permissions differ; withdrawal/transfer-like scopes disabled | no public sandbox/testnet was confirmed in checked official pages |

Official-source anchors used for the requirement profile include Binance
developer docs, Bybit v5 docs, OKX docs-v5, Bitget API docs, Gate APIv4 docs,
KuCoin authentication docs, HTX/Huobi API docs, BingX API/support docs,
BitMart developer docs, Kraken Spot/Futures docs, Bitvavo REST docs, and
Hyperliquid developer docs. If a future adapter needs executable behavior, use
the official requirement as a checklist, then add a local fixture, sandbox, or
testnet artifact before changing `support_level`.

## Candidate exchange matrix

| Exchange | Spot | Futures | Margin mode from Freqtrade docs | Stoploss on exchange from Freqtrade docs | Market-order note | Trailing stop | NFI Engine level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Binance | documented | documented | futures: isolated, cross | spot: limit; futures: market, limit | USD-M Futures has signed balance plus test-order proof; spot uses mode-scoped fixture proof | not profiled | `verified` |
| Bingx | documented | not in overview table | not in overview table | spot: market, limit | market stoploss documented for spot; mode-scoped fixture proof is checked in | not profiled | `verified` |
| Bitmart | documented | not in overview table | not in overview table | spot: not available | market stoploss not documented in overview; mode-scoped fixture proof is checked in | not profiled | `verified` |
| Bitget | documented | documented | futures: isolated | spot: market, limit; futures: market, limit | market stoploss documented; mode-scoped fixture proof is checked in | not profiled | `verified` |
| Bybit | documented | documented | futures: isolated | spot: not available; futures: market, limit | testnet adapter covers sandbox enablement, market/limit order mapping, balance fetch, cancel/fetch order, funding fallback, and typed reject paths | not profiled | `verified` |
| Gate.io | documented | documented | futures: isolated | spot: limit; futures: limit | market stoploss not documented in overview; mode-scoped fixture proof is checked in | not profiled | `verified` |
| HTX | documented | not in overview table | not in overview table | spot: limit | market stoploss not documented in overview; mode-scoped fixture proof is checked in | not profiled | `verified` |
| Hyperliquid | documented | documented | futures: isolated, cross | spot: not available; futures: limit | market orders require separate operator caution; mode-scoped fixture proof is checked in | not profiled | `verified` |
| Kraken | documented | separate Kraken Futures id | not in overview table | spot: market, limit | market stoploss documented for spot; mode-scoped fixture proof is checked in | not profiled | `verified` |
| Kraken Futures | not applicable | documented | futures: isolated | futures: market, limit | market stoploss documented for futures; mode-scoped fixture proof is checked in | not profiled | `verified` |
| OKX | documented | documented | futures: isolated | spot: limit; futures: limit | market stoploss not documented in overview; mode-scoped fixture proof is checked in | not profiled | `verified` |
| Bitvavo | documented | not in overview table | not in overview table | spot: not available | market stoploss not documented in overview; mode-scoped fixture proof is checked in | not profiled | `verified` |
| Kucoin | documented | not in overview table | not in overview table | spot: market, limit | market stoploss documented for spot; mode-scoped fixture proof is checked in | not profiled | `verified` |

## Generic-unverified path

NFI Engine accepts additional exchange ids through the report-only capability
discovery boundary:

```bash
uv run nfi-engine exchange capabilities --exchange mexc --trading-mode futures --format json
```

Unknown ids are labeled `generic-unverified`, `source=generic-discovery`, and
`can_configure=false`. This does not promote the exchange into config,
paper/testnet, or live execution. Config validation still returns
`EXCHANGE_UNSUPPORTED` until a real registry profile and local evidence exist.
Because arbitrary ids have unknown credential models, generic reports leave
`credential_fields=[]` instead of guessing `api_key` / `api_secret`.

The result must remain `generic-unverified` until there is local evidence for:

- market metadata fetch.
- account/wallet balance fetch with redacted credentials.
- spot/futures/margin capability detection.
- stoploss and market-order capability detection.
- testnet or sandbox behavior when the exchange provides it.
- fixture replay for failure cases such as stale data, rejected order types, API
  lag, and permission denial.

## Credential boundary

Exchange setup means exchange API credentials or exchange-specific signing
credentials. It never means the local operator password, internal API token,
wallet seed phrases, main wallet private keys, or withdrawal keys. For exchanges
with special credential models, such as Hyperliquid, NFI Engine must present the
requirement as a high-risk exchange credential path and keep live mode blocked
until a separate permission and sandbox proof exists.

Runtime config, setup preview, and one-command install accept the documented
special fields: `passphrase`, `memo`, `operator_id`, `account_address`, and
`api_wallet_signer`. These values are write-only in the operator UI and are
redacted from config preview responses, support bundles, and installer output.
The one-command installer rejects secret-bearing process arguments; use a
`0600` credentials file or `NFI_ENGINE_SETUP_*` environment variables.

## Runtime registry contract

The runtime registry stores each capability as data, not as hard-coded UI
branches. The registry spine lives in
`src/nfi_engine/exchange/capability_models.py`,
`src/nfi_engine/exchange/seed_profiles.py`,
`src/nfi_engine/exchange/capabilities.py`,
`src/nfi_engine/config/validators.py`, and
`src/nfi_engine/preflight/exchange_checks.py`.

- exchange id and display name.
- `verified`, `candidate`, or `generic-unverified` level.
- spot, futures, and margin capability.
- stoploss-on-exchange mode.
- market-order support.
- trailing-stop, testnet, sandbox, and data-only availability.
- credential fields required.
- exchange-specific credential fields required by official docs.
- evidence artifact path and checked date.
- official-doc requirement metadata for setup fields, permission notes, testnet
  notes, order notes, and checked date.

`nfi-engine exchange capabilities` emits a typed JSON/text capability document
for registry profiles and arbitrary report-only ids. Config/preflight validation
consume only executable registry profiles. As of 2026-06-26, every registered
exchange/mode emitted by `nfi-engine exchange runtime-check --all --format json`
has checked-in mode-scoped fixture evidence. Live exchange orders remain blocked
by normal live gates and are outside this promotion claim.
