# Release Status

Date: 2026-06-28 KST
Current review note: 2026-06-28 KST

This document is the current status summary for the evidence-backed
paper/testnet release-candidate lane. It is not approval for real-money live
order execution.

## Verdict

The RC lane is approved for local paper/testnet evaluation within the documented
safety boundary. It is not approval for real-money live order execution. The
latest 2026-06-28 pass keeps the 2026-06-26 Docker final-smoke publication
evidence, adds a secret-safe reusable priority-exchange credential probe,
adds an executable testnet-only pilot readiness report, and adds a repeatable
Pi4 soak probe wrapper. Real priority-exchange testnet keys are still required
before real exchange API evidence can replace `blocked-no-key`.

```text
.omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/
.omo/evidence/2026-06-26-nfi-engine-final-product-publication/
.omo/evidence/2026-06-28-remaining-tracks/
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
- `scripts/testnet_credential_probe.sh`: repeatable secret-safe probe for
  Binance, Bybit, OKX, and Bitget testnet credential readiness. It reports
  `blocked-no-key` when no owner-only credential source is present. It can
  create empty owner-only per-exchange templates with `--init-template`; real
  API values still must be supplied locally by the operator.
- `nfi-engine exchange testnet-pilot --config ...`: executable testnet-only
  readiness report for profile, live lock, testnet scope, credentials,
  permission hardening, reconciliation, circuit breakers, X7 runtime,
  idempotency, and order-state coverage. It keeps
  `live_money_orders_enabled=false`.
- `scripts/pi4_soak.sh`: repeatable non-mutating Pi4 profile loop built on
  `scripts/pi4_rc_profile.sh`. A long-running soak still needs fresh wall-clock
  runtime evidence from the target device.
- `final-smoke.txt`: 2026-06-28 `bash scripts/final_smoke.sh` exited `0`,
  including Docker install, `/api/v1/ping`, auth denial, authenticated
  dashboard/home fetch, safe uninstall, and purge uninstall.
- `pi4-ssh-probe.txt`: 2026-06-28 key-based SSH probe reached the Pi and
  captured `temp=49.6'C`, `throttled=0xe0000`.
- `final-gate/pytest.txt`: 2026-06-28 full test suite `556 passed`.
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
- Testnet-only pilot readiness is now executable as a CLI report, including a
  stable sample client order id and a closed order-state list. It does not
  submit exchange orders.

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
- Pi4 soak automation is present, but multi-hour or multi-day evidence must be
  captured on the target hardware after the operator starts the soak window.

## Blocked Or Not Done

- Real-money live order execution remains blocked pending a separate approved
  live-execution plan.
- Blocked: public Freqtrade superiority, profit, safety guarantee, upstream X7
  trade parity, and public Pi4 performance comparison claims.
- Real exchange credentials must be re-entered by the operator in local runtime
  secret storage; they are not recoverable from sanitized RC evidence.
- Real Binance, Bybit, OKX, and Bitget testnet credential checks are blocked
  until safe testnet keys are supplied through local secret storage.
- A GitHub release tag can be cut after the 2026-06-28 quality gates pass and
  the release notes are checked against `docs/release-wording.md`.
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
