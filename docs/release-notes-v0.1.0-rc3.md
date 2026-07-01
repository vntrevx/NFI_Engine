# v0.1.0-rc3 Release Notes

Date: 2026-07-02 KST

`v0.1.0-rc3` supersedes `v0.1.0-rc2` with the CI fallback test fix included.
It is still a paper/testnet release candidate, not a live-ready release.

## Included since rc2

- CI fix for clean checkouts where the optional Vite React distribution is not
  present: the persistence/dashboard integration test now accepts the
  server-rendered home fallback contract as well as the React shell contract.
- Main-branch CI passed after the fix.
- Repository cleanup removed the internal root `DESIGN.md` file and the
  superseded `v0.1.0-rc2` release-note file from the published tree.

## Included from rc2

- Durable execution ledger records, repositories, and bounded read models for
  order intents, exchange orders, fills, and execution events.
- Testnet execution state-machine coverage with idempotency, terminal-state
  guards, partial-fill handling, and reconciliation events.
- Binance-first live canary preview/execution gate implementation with explicit
  preview hash, owner confirmation phrase, fixed notional, immediate reduce-only
  exit path, ledger recording, redaction, and fake-client tests.
- Runtime-health checks for heartbeat, database, wallet/market freshness,
  reconciliation age, exchange API errors, circuit-breakers, disk, memory, and
  restricted live-pilot blockers.
- Protected read-only account-truth/dashboard API surfaces for balance,
  exposure, open/closed PnL, W/L, execution lifecycle, reconciliation status,
  and safety signals.
- Operator UI/frontend refresh with localized truth panels and safety signal
  visibility.
- Pi4/testnet probe tooling hardening and a GitHub exchange-test report template.
- Updated release/safety docs for the 2026-07 paper/testnet RC boundary.

## Boundary

- This release candidate is not live-ready.
- No real live canary has passed.
- No canary-pass marker exists.
- No restricted live pilot has run.
- Owner Binance testnet keys remain required for real testnet exchange evidence.
- Owner live credentials and explicit approval remain required before any real
  live-canary execution.
- Fresh connected-Pi4 validation is currently blocked by `PI4_THROTTLED` and
  `PI4_UV_MISSING`; public current-Pi4 performance claims are not supported.
- Bybit, OKX, and Bitget remain template/issue-driven expansion lanes until safe
  keys or redacted user reports justify deeper validation.

## Verification

Local verification before the fix push:

```bash
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest -q
uv run python scripts/release_wording_scan.py
git diff --check
```

Observed local results included `643 passed` for pytest, `0 errors` from
basedpyright, and `violations=0` from the release wording scan.

GitHub Actions CI passed on main and on the `v0.1.0-rc3` tag after the fallback
test fix.
