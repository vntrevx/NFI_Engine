# Exchange Support Matrix

This matrix converts Freqtrade-documented exchange coverage into NFI Engine
capability levels. It does not mean every exchange is verified in NFI Engine.

Source checked on 2026-06-14. Bybit local testnet adapter evidence checked on
2026-06-21:
`https://www.freqtrade.io/en/stable/exchanges/`.

## Verification levels

| Level | Meaning | Live-mode rule |
| --- | --- | --- |
| `verified` | NFI Engine has exact exchange evidence from fixture, testnet, or sandbox runs. | Live can only proceed through normal live gates after preflight, credential audit, balance cap, circuit breaker, and reconciliation checks. |
| `candidate` | The exchange appears in Freqtrade's documented support table, but NFI Engine has not promoted it with local evidence. | Dry-run/paper research only; live remains blocked until promoted. |
| `generic-unverified` | A broader CCXT-style or custom exchange id can be configured/probed later, but is not first-class. | Live blocked; capability discovery may produce a report, not a trade path. |

Promotion rule: never promote an exchange from `candidate` or
`generic-unverified` to `verified` from a docs table alone. Promotion requires
a named artifact under `.omo/evidence/` or a checked-in deterministic fixture.

## Candidate exchange matrix

| Exchange | Spot | Futures | Margin mode from Freqtrade docs | Stoploss on exchange from Freqtrade docs | Market-order note | Trailing stop | NFI Engine level |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Binance | documented | documented | futures: isolated, cross | spot: limit; futures: market, limit | market stoploss documented for futures; entry/exit market profile not verified locally | not profiled | `candidate` |
| Bingx | documented | not in overview table | not in overview table | spot: market, limit | market stoploss documented for spot; entry/exit market profile not verified locally | not profiled | `candidate` |
| Bitmart | documented | not in overview table | not in overview table | spot: not available | market stoploss not documented in overview | not profiled | `candidate` |
| Bitget | documented | documented | futures: isolated | spot: market, limit; futures: market, limit | market stoploss documented; entry/exit market profile not verified locally | not profiled | `candidate` |
| Bybit | documented | documented | futures: isolated | spot: not available; futures: market, limit | testnet adapter covers sandbox enablement, market/limit order mapping, balance fetch, cancel/fetch order, funding fallback, and typed reject paths | not profiled | `verified` |
| Gate.io | documented | documented | futures: isolated | spot: limit; futures: limit | market stoploss not documented in overview | not profiled | `candidate` |
| HTX | documented | not in overview table | not in overview table | spot: limit | market stoploss not documented in overview | not profiled | `candidate` |
| Hyperliquid | documented | documented | futures: isolated, cross | spot: not available; futures: limit | Freqtrade notes that market orders are simulated by ccxt; NFI Engine must verify this separately | not profiled | `candidate` |
| Kraken | documented | separate Kraken Futures id | not in overview table | spot: market, limit | market stoploss documented for spot; entry/exit market profile not verified locally | not profiled | `candidate` |
| Kraken Futures | not applicable | documented | futures: isolated | futures: market, limit | market stoploss documented for futures; entry/exit market profile not verified locally | not profiled | `candidate` |
| OKX | documented | documented | futures: isolated | spot: limit; futures: limit | market stoploss not documented in overview | not profiled | `candidate` |
| Bitvavo | documented | not in overview table | not in overview table | spot: not available | market stoploss not documented in overview | not profiled | `candidate` |
| Kucoin | documented | not in overview table | not in overview table | spot: market, limit | market stoploss documented for spot; entry/exit market profile not verified locally | not profiled | `candidate` |

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
credentials. It never means the local login token, wallet seed phrases, main
wallet private keys, or withdrawal keys. For exchanges with special credential
models, such as Hyperliquid, NFI Engine must present the requirement as a
high-risk exchange credential path and keep live mode blocked until a separate
permission and sandbox proof exists.

## Runtime registry contract

The runtime registry now stores each capability as data, not as hard-coded UI
branches. S4 implemented the first registry spine in
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
- evidence artifact path and checked date.

As of 2026-06-15, `nfi-engine exchange check` can inspect a config-backed
profile or a direct `--exchange` id such as `generic-ccxt`.
`nfi-engine exchange capabilities` emits a typed JSON/text capability document
for registry profiles and arbitrary report-only ids. Config/preflight validation
consume only executable registry profiles. The seeded Freqtrade-documented
exchanges remain `candidate` until NFI Engine has its own fixture, sandbox, or
testnet proof. As of 2026-06-21, the local deterministic simulator and the
Bybit testnet adapter lane are promoted to `verified`; live exchange orders are
still blocked by the current milestone policy.
