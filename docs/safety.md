# Safety Guardrails

NFI Engine M1 is limited to simulator, paper, and testnet workflows. Confirmed live
configuration can be parsed for validation, but runtime commands reject it with
`LIVE_TRADING_OUT_OF_SCOPE`.

When `engine.live_trading=true`, preflight now also emits live-readiness hardening
checks without unlocking real-money execution:

- `LIVE_EXCHANGE_CREDENTIALS` confirms API key fields are present without printing
  secret values.
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

Current RC evidence, including the 2026-06-22 Pi4 T5A benchmark resolution,
supports paper/testnet operation only. It does not change the live-order lock,
credential-permission audit requirement, reconciliation requirement, circuit
breaker requirement, or manual halt requirement.

The API defaults to `127.0.0.1`, does not enable CORS by default, and rejects weak
operator tokens outside local/dev/test environments. Config and support surfaces redact
API tokens and exchange credentials as `REDACTED`.

Futures mode emits operator warnings for the one-bot-per-account assumption, leverage
risk, and cross-margin account risk. These warnings are surfaced through the typed
`safety` service so later UI and preflight tasks can expose them without copying trading
logic.
