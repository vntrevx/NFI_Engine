# NFI X7 Compatibility Boundary

This document records the clean-room compatibility target for NFI Engine. It is
a product contract for adapter behavior, not a copy plan for upstream strategy
logic.

## Clean-room provenance

- External target: `https://github.com/iterativv/NostalgiaForInfinity/blob/main/NostalgiaForInfinityX7.py`.
- Refreshed on: 2026-06-20.
- Observed upstream commit: `e9b601b0b3efe342b5ab14205da71e054625121d`.
- Observed raw sha256: `6ee4253f805229f9e7d38e6045c8f623f839fa1fc154b9c8aca0049d8515c3bf`.
- Observed raw strategy version: `v17.4.258`.
- Parent plan note: earlier 2026-06-14 observations are superseded by this
  refreshed 2026-06-20 observation.
- NFI Engine uses public behavior, callback names, and runtime shape as the
  reference. It does not vendor, translate, rename, or paste upstream code.
- Do not copy Freqtrade, FreqUI, NostalgiaForInfinity source, docs prose,
  strategy internals, parameter trees, tag lists, or UI patterns.

## NFI X7 target facts

| Fact | Observed target | NFI Engine interpretation |
| --- | --- | --- |
| Strategy class | `NostalgiaForInfinityX7` | External target name for reports only. |
| Freqtrade interface | `INTERFACE_VERSION = 3` | Compatibility adapter should understand interface-v3-shaped callbacks. |
| Version | `v17.4.258` | Report metadata only; never a vendored implementation version. |
| Base timeframe | `5m` | Clean-room fixtures and reports should default to 5-minute base candles. |
| Informative timeframes | `15m`, `1h`, `4h`, `1d`; BTC informatives observed separately | Data-provider contract must make multi-timeframe availability explicit. |
| Trading surface | Freqtrade strategy callbacks plus long/short signal columns | NFI Engine should model callback availability and signal columns, not upstream conditions. |

## Supported

Supported means the current engine has a concrete clean-room surface or an
adapter contract that can be exercised without upstream code.

| Surface | Status | Boundary |
| --- | --- | --- |
| Strategy identity metadata | Supported | Reports may mention `NostalgiaForInfinityX7`, `INTERFACE_VERSION`, `v17.4.258`, and `5m` as observed facts. |
| Core signal callbacks | Supported shape | `populate_indicators`, `populate_entry_trend`, and `populate_exit_trend` are adapter-level callback names. The engine must not copy the upstream indicator graph. |
| Signal columns | Supported shape | Clean-room fixtures may expose long/short entry and exit signals with generic tags. |
| Base timeframe | Supported default | `5m` is the compatibility baseline for NFI-shaped reports and fixtures. |
| Sandbox boundary | Supported | User-supplied strategy loading remains behind the local sandbox/import policy. |
| Report wording | Supported | Reports may say a callback is present, absent, supported, partial, or excluded. They must not claim trade parity. |
| Compatibility report harness | Supported | `nfi-engine sandbox check --output` writes a clean-room JSON report for local strategy specs. |
| Native positioning decisions | Supported shape | `custom_stake_amount`, `leverage`, `order_filled`, and `adjust_trade_position` now route through typed engine-owned stake, leverage, fill snapshot, and bounded adjustment decisions. |
| Native protections and confirmations | Supported shape | `confirm_trade_entry`, `confirm_trade_exit`, pair-lock, cooldown, stale-data, circuit-breaker, live-confirmation, and bounded `bot_loop_start` decisions route through typed engine-owned guards with no hidden network I/O or raw config mutation. |
| Native backtest timeline | Supported shape | Deterministic backtest JSON records native X7 entry reasons such as `x7-long-momentum-balanced` without fixture `signal_side` fields. |
| Native paper timeline | Supported shape | X7 paper runs load the configured native strategy adapter, derive visible OHLCV rows from ticks, record semantic entry reasons without fixture `signal_side`, and keep fixture signals only for explicit demo/legacy runs. Paper orders remain simulated and pass through existing risk caps such as `max_open_trades`. |
| Native paper safety gates | Supported shape | X7 paper startup runs preflight, fetches wallet balance through the exchange adapter boundary, passes the resulting account snapshot into risk quotes, and blocks unsafe leverage before strategy timelines or simulated orders are created. HTTP wallet/runtime health surfaces expose the same local safety state. |
| Native semantic runtime install path | Supported shape | `examples/x7-futures-paper.yaml`, `nfi_engine.strategy.nfi_x7:X7NativeStrategy`, final smoke, and the release wording scan exercise the dry-run/paper/testnet path without Freqtrade as a runtime dependency. |
| Pi4 RC benchmark/resource gate | Supported shape | The 2026-06-22 T5A evidence resolves the native X7 backtest sample warning on the measured Pi4 without raising the `1000 ms` budget. `claim_allowed=false` remains. |

## Partial

Partial means NFI Engine can name the surface, but product behavior still needs
typed contracts, fixtures, and runtime evidence before it becomes verified.

| Surface | Current partial scope | Required next evidence |
| --- | --- | --- |
| `informative_pairs` | Callback name can be detected; visible-row and missing-frame contracts are tested. | Multi-timeframe fixture with missing-data, stale-data, and pair metadata cases. |
| Multi-timeframe indicators | Target facts are known; upstream indicator internals are excluded. | Clean-room strategy fixture that consumes separate base/informative frames. |
| `custom_exit` | Callback is part of the target surface; full Freqtrade exit semantics are not verified. | Typed exit callback result model and deterministic backtest/paper replay. |
| `custom_stake_amount` | Native stake decision caps proposed stake to allocation and available-balance inputs, and paper startup now feeds fetched wallet snapshots into risk requests. | Testnet exchange-adapter evidence for non-simulator wallet snapshots and capability-specific allocation limits. |
| `adjust_trade_position` | Native adjustment decisions are disabled by default and bounded when explicit max/available inputs exist. | Position timeline model with circuit-breaker behavior. |
| `leverage` | Native default is 3x and the decision can cap against a supplied max; `risk.quote_order` enforces configured max leverage. | Exchange capability profile evidence flowing into runtime requests. |

## Excluded

Excluded means the work is intentionally out of scope for this product boundary.

| Exclusion | Reason |
| --- | --- |
| Vendoring upstream `NostalgiaForInfinityX7.py` | The project is clean-room and the upstream file is not vendored. |
| Copying indicator conditions, parameter blocks, tags, pair filters, or blacklist internals | These are upstream strategy internals, not a public adapter contract. |
| Full NFI X7 trade parity | Market data, exchange details, Freqtrade internals, and upstream strategy internals make parity an unsafe claim. |
| Profitability or performance superiority claims | Requires separate measured evidence and still cannot imply future returns. |
| Freqtrade DB, wallet, plugin, or runtime internals | NFI Engine keeps native storage, risk, sandbox, and operator flows. |
| Live exchange orders from strategy callbacks | Live mode remains behind explicit setup, preflight, exchange capability checks, balance caps, circuit breakers, reconciliation, kill switch, and user confirmation. |

## Product rule

The compatibility goal is simple: NFI Engine should make NFI-shaped strategy
research easy, deterministic, and safe on low-resource hardware while keeping
the implementation original. If a future report says `verified`, the proof must
point to a local fixture, testnet/sandbox run, or deterministic replay artifact.

Public wording that references this compatibility boundary must follow
[release-wording.md](release-wording.md), including evidence links
for any parity, performance, or readiness statements.

Current local evidence for this boundary is grouped under:

```text
.omo/evidence/2026-06-20-nfi-x7-semantic-port/
.omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/
```

Current release-candidate status:

- `coverage_state=verified`, `pending_modules=[]`, and native X7 semantic
  evidence are available for paper/testnet operation.
- Raspberry Pi 4 evidence exists for install/bootstrap, M2/X7 benchmark,
  paper soak, reversible deployment, and T5A budget resolution on the measured
  device.
- Live exchange orders remain excluded until a separate live-execution plan is
  approved and verified.
