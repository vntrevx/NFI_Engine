# Release Status

Date: 2026-06-26 KST
Current review note: 2026-06-26 KST

This document is the current status summary for the evidence-backed
paper/testnet release-candidate lane. It is not approval for real-money live
order execution.

## Verdict

The RC lane is approved for local paper/testnet evaluation within the documented
safety boundary. It is not approval for real-money live order execution. The
latest 2026-06-26 publication pass adds fresh Docker final-smoke evidence,
install/uninstall dry-run receipts, a non-mutating Pi4 health probe, and a
secret-safe real-testnet credential lane that is blocked by missing keys.

```text
.omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/
.omo/evidence/2026-06-26-nfi-engine-final-product-publication/
```

Final local gates under that root include:

- `f1-plan-compliance.md`: plan items 1-14 covered, plan evidence verified.
- `f3-real-manual-qa.md`: final smoke drove CLI, API, Docker, browser, backup,
  paper-run, and X7 inspect surfaces.
- `f4-scope-fidelity.md`: final verdict is paper/testnet RC only.
- `ulw-reconcile-g050/f3-current-manual-qa.md`: current 2026-06-23 F3 rerun
  keeps CLI/browser/paper/release checks passing, but records the external
  Docker Desktop/WSL blocker for the fresh final Docker smoke.
- `ulw-reconcile-g063/summary.assertions.json`: current 2026-06-23 Pi4 RC
  profile reconciliation keeps the reversible deploy boundary valid without a
  fresh SSH deploy mutation.
- `ulw-reconcile-g072/summary.assertions.json`: current 2026-06-24 UI review
  keeps no-forced-refresh language/runtime behavior, browser security probes,
  and desktop/mobile visual QA passing.
- `t6-final-smoke.txt`: 2026-06-26 `bash scripts/final_smoke.sh` exited `0`,
  including Docker install, `/api/v1/ping`, auth denial, authenticated
  dashboard/home fetch, safe uninstall, and purge uninstall.
- `t6-install-uninstall.txt`: local shell install, safe uninstall, and purge
  uninstall dry-runs exited `0`.
- `t6-pi4-install-docker.md`: Pi4 SSH health was reachable and cool for the
  captured probe, but historical throttle flags keep public Pi4 performance
  claims blocked.
- `t8-real-testnet-credentials.md`: Binance, Bybit, OKX, and Bitget real
  testnet credential checks are `blocked-no-key`; no raw secret values were
  printed and no real exchange API call was attempted.
- `final-gate/pytest.txt`: `497 passed`.
- `final-gate/release-wording-scan-final.txt`: `violations=0`.

## Completed

- Native clean-room X7 semantic inspection remains verified with
  `pending_modules=[]`.
- Paper/testnet setup has CLI, API, browser, Docker, and Pi4 evidence.
- Operator workflow covers exchange selection, exchange API credentials,
  recommended 3x leverage, explicit wallet balance fetch, allocation amount,
  spot/futures intent, dry-run intent, live preview blocking, preflight, and
  start/pause/resume/stop controls.
- Wallet setup means exchange API credentials only. It does not mean wallet
  seed phrases; it does not mean private keys, withdrawal keys, or local login
  tokens.
- UI state changes no longer require forced refresh in the covered operator
  paths. G072 verifies EN -> KO -> EL -> EN locale changes, runtime
  start/pause/resume/stop controls, local-only browser requests, and
  desktop/mobile KO/EL screenshots with no overflow.
- One-line shell, npm, and Bun install/uninstall paths were previously
  re-verified in G011, and the 2026-06-26 T6 pass rechecked shell
  install/uninstall dry-runs plus full Docker final smoke.
- Pi4 RC checks include user-home toolchain staging, benchmark budget
  resolution, 500-tick X7 paper soak, loopback deployment profile, stock-host
  rollback receipts, no throttling in the captured runs, and G063 revalidation
  of the non-mutating `pi4_rc_profile` edge path.
- Release wording policy blocks unsupported claims and the deterministic scan
  currently reports zero violations.
- Public docs now describe username/password operator login instead of the old
  token-paste login flow.

## Partial

- Pi4 is an internal RC lane for the measured hardware. The 2026-06-26 probe was
  reachable with low load, 44.8C temperature, and large memory headroom, but
  historical throttle flags keep public speed or performance claims blocked.
- The update button is proof-only: preview/apply/rollback receipts exist, but
  automatic GitHub source mutation remains outside this RC.
- Exchange support is capability/evidence promoted. Candidate and
  generic-unverified exchanges remain blocked from runtime trade paths until
  fixture, sandbox, or testnet evidence promotes them.
- Registered exchange modes have deterministic fixture/sandbox/report-only
  runtime evidence, but real priority-exchange testnet credentials were not
  available in T8, so live-like balance/order validation remains `blocked-no-key`.
- The dashboard is usable as an operator cockpit, but richer position, account,
  PnL, and risk compression still belongs to later work.

## Blocked Or Not Done

- Real-money live order execution remains blocked pending a separate approved
  live-execution plan.
- Blocked: public Freqtrade superiority, profit, safety guarantee, upstream X7
  trade parity, and public Pi4 performance comparison claims.
- Real exchange credentials must be re-entered by the operator in local runtime
  secret storage; they are not recoverable from sanitized RC evidence.
- Real Binance, Bybit, OKX, and Bitget testnet credential checks are blocked
  until safe testnet keys are supplied through local secret storage.
- Multi-OS install/uninstall repetition beyond the current matrix still needs
  more evidence.

## Publication Boundary

- README and release notes may say paper/testnet RC, native NFI-shaped X7
  runtime, evidence-backed deterministic exchange lanes, and fresh 2026-06-26
  local Docker smoke.
- README and release notes must not say live-money ready, profit-capable,
  guaranteed safe, comparative superiority, full upstream X7 trade parity, all
  exchanges fully supported, or public Pi4 performance proven.
- Live-execution design is limited to a separate testnet-only pilot boundary in
  `docs/safety.md`; it does not unlock real-money orders.
