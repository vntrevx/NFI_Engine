# Safety Guardrails

NFI Engine is currently limited to simulator, paper, and testnet workflows.
Confirmed live configuration can be parsed for validation, but default runtime
commands reject unrestricted live execution with `LIVE_TRADING_OUT_OF_SCOPE`.

When `engine.live_trading=true`, preflight now also emits live-readiness hardening
checks without unlocking real-money execution:

- `LIVE_EXCHANGE_CREDENTIALS` confirms exchange credential fields are present
  without printing secret values.
- `LIVE_PERMISSION_HARDENING` blocks unknown or unsafe live API permissions, including
  missing read/trade/futures permission, enabled or unknown withdrawal permission, and
  missing IP allowlist proof.
- `LIVE_RECONCILIATION_HARDENING` requires startup reconciliation to be explicitly
  configured.
- `LIVE_CIRCUIT_BREAKER_HARDENING` requires circuit breakers, positive loss/freshness
  budgets, and a manual halt file.
- `LIVE_STRATEGY_HARDENING` requires the native X7 strategy and complete semantic
  coverage evidence.

Passing these hardening checks does not enable live orders. The milestone live lock
still blocks startup until a separate live-execution milestone is designed, reviewed,
and verified.

Current backend-reliability and 2026-07 next-phase evidence covers protected
read-only account truth, execution lifecycle read models, reconciliation mismatch
blocking, testnet order-test safety lanes, runtime-health machine checks, a
non-mutating Pi4/local soak path, a fake-client-proven live canary execution
gate, restricted live pilot startup guards, publish-boundary classification,
owner-key testnet blocker restatement, and a decision-only live-gate packet. It
still does not enable general real-money orders. WP5.3 recorded
`blocked-no-live-credentials`, WP6.2 recorded
`blocked-awaiting-owner-live-approval`, and WP11 created no canary-pass marker;
no real live canary or restricted live 24h pilot has run. A 2026-07-02 local
final smoke passed Docker install, ping, auth denial, authenticated home and
dashboard fetch, safe uninstall, and purge.

## Testnet-Only Live Execution Design Boundary

The next live-execution milestone is a Binance-first testnet-only pilot design,
not a real-money order switch. Binance is the owner-primary deep path because it
is the current operator venue; Bybit, OKX, and Bitget stay as template and
issue-driven expansion lanes until safe testnet credentials or user reports
justify deeper validation. The pilot must keep `engine.live_trading=true`
blocked for production credentials until all of the following controls have
executable evidence:

- order state machine: `intent_created`, `risk_checked`, `submitted`,
  `acknowledged`, `partially_filled`, `filled`, `cancel_requested`, `canceled`,
  `rejected`, `expired`, and `reconciled`.
- reconciliation: startup and periodic exchange/account reconciliation must
  compare local orders, exchange orders, fills, balances, and open positions
  before new entries are allowed.
- idempotency: every order intent must carry a stable client id and idempotency
  key so retries cannot duplicate an exchange order.
- kill switch: a local manual halt file and authenticated API halt must block
  new entries immediately and preserve inspectable state.
- circuit breaker: loss, freshness, reconciliation mismatch, exchange error
  rate, stale price, and position exposure breakers must stop new orders before
  submission.
- partial-fill/cancel/reject handling: partial fills must update remaining
  quantity and exposure; cancel and reject states must be terminal unless a new
  operator-reviewed intent is created.
- rollback/disable: the operator must be able to disable the pilot, roll back to
  dry-run/paper config, and preserve an audit trail without deleting evidence.
- dashboard visibility: the operator cockpit must expose order lifecycle,
  reconciliation, idempotency, kill switch, circuit-breaker, and partial-fill
  exposure signals without requiring raw logs.

The design boundary may support testnet order-lane evidence. It must not
enable real-money orders, weaken live blockers, or bypass credential permission
checks.

The executable readiness surface for this boundary is:

```bash
uv run nfi-engine exchange testnet-pilot --config examples/x7-futures-paper.yaml --json
```

The report is a gate summary, not an order-placement command. It checks the
exchange profile, live lock, testnet scope, credential presence, permission
hardening, reconciliation requirement, circuit breakers, native X7 runtime,
idempotency id shape, order-state coverage, and dashboard safety signal coverage
while keeping
`live_money_orders_enabled=false`.

Current RC evidence supports paper/testnet operation plus a preview-only,
owner-confirmed live canary command whose execution path is fake-client proven.
WP5.3 records that no owner live credentials were available, so no real canary
pass exists. It does not change the general live-order lock,
credential-permission audit requirement, reconciliation requirement, circuit
breaker requirement, manual halt requirement, owner confirmation requirement, or
rollback evidence requirement.

Restricted live pilot mode is a separate guarded state, not unrestricted live
trading. It requires a sanitized live-canary pass marker, explicit pair allowlist,
stake, leverage, max-open-trades, daily loss cap, manual halt file,
reconciliation interval, wallet sync interval, and runtime duration. Runtime
health reports `LIVE_PILOT` blocked when the marker, freshness, breaker, or
explicit config gates fail; runtime control refuses new entries while health is
blocked.
WP6.2 records the restricted live 24h soak as
`blocked-awaiting-owner-live-approval`. That blocker preserves the distinction
between paper/testnet evidence, canary-ready implementation, restricted pilot
guards, and general live trading.

The API defaults to `127.0.0.1`, does not enable CORS by default, and rejects weak
operator credentials outside local/dev/test environments. Config and support
surfaces redact API tokens, operator passwords, and exchange credentials as
`REDACTED`.

Futures mode emits operator warnings for the one-bot-per-account assumption, leverage
risk, and cross-margin account risk. These warnings are surfaced through the typed
`safety` service so later UI and preflight tasks can expose them without copying trading
logic.
