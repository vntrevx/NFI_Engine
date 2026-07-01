# Release Status

Date: 2026-07-02 KST
Current review note: 2026-07 next-phase WP12 publish-readiness continuation

This document is the current status summary for the evidence-backed
paper/testnet release-candidate lane. It is not approval for real-money live
order execution.

## Verdict

The RC lane is approved for local paper/testnet evaluation within the documented
safety boundary. It is not approval for real-money live order execution. The
2026-07 next-phase evidence adds an RC/publish freeze, fresh connected-Pi4
revalidation blockers, owner-key testnet proof restatement, protected
account/dashboard truth recheck, and a decision-only live-gate packet. The
boundary remains canary-ready implementation only, not live-canary-passed or
production-live. Owner Binance testnet keys, owner-approved live canary
execution, a sanitized canary-pass marker, and any restricted live runtime remain
separate gates; Bybit, OKX, and Bitget remain template/issue-driven expansion
lanes.

```text
.omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/
.omo/evidence/2026-06-26-nfi-engine-final-product-publication/
.omo/evidence/2026-06-28-remaining-tracks/
.omo/evidence/2026-06-30-backend-reliability-live-engine/
.omo/evidence/2026-07-next-phase/
```

Selected local gates and evidence under those roots include:

2026-07 next-phase continuation evidence:

- `wp7-rc-freeze/`: dirty-tree classification, publish allowlist, local-only
  denylist, release-wording precheck, and unstaged/no-commit boundary.
- `wp8-pi4-fresh-revalidation/`: fresh connected-Pi4 intake blocked by
  `PI4_THROTTLED` and `PI4_UV_MISSING`; historical Pi4 RC evidence remains
  internal and cannot be used as current public Pi4 proof.
- `wp9-owner-key-testnet/`: owner-key lane remains
  `blocked-owner-testnet-keys`; direct pilot/execute checks keep
  `live_money_orders_enabled=false`.
- `wp10-account-dashboard-truth/`: focused dashboard, reconciliation, protected
  API, runtime-health, malformed metadata, and redaction checks passed.
- `wp11-canary-pilot-decision/`: live-canary decision packet only; no preview
  without owner config, no live order, no restricted pilot runtime, and no marker
  creation.
- `wp12-publish-readiness/`: final summary, publish boundary, docs review,
  blocker list, and release-wording scan for this continuation.


- `final/f1-plan-compliance.md`: current plan evidence check reports
  `PLAN_EVIDENCE_OK referenced=21 missing=0`.
- `final/f2-code-quality-review.md`: strict gates passed (`ruff`,
  `basedpyright`, `uv run pytest -q` with 640 passed, release wording scan with
  zero violations, and `git diff --check`).
- `final/f3-real-manual-qa.md`: manual QA fetched authenticated
  API/dashboard/runtime-health surfaces, proved reconciliation mismatch blocking,
  testnet pilot/readiness blockers, fake Binance order-test adapter behavior,
  redaction, local Pi4 soak blockers, live canary preview, and restricted live
  pilot blocking. Docker remains locally blocked by missing WSL Docker
  integration.
- `final/f4-scope-fidelity.md`: final verdict is paper/testnet RC plus guarded
  canary/restricted-pilot implementation with honest live blockers, not
  live-ready.
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
- `nfi-engine exchange testnet-pilot --config ...`: executable Binance-first
  testnet-only readiness report for profile, live lock, testnet scope,
  credentials, permission hardening, reconciliation, circuit breakers, X7
  runtime, idempotency, order-state coverage, and dashboard safety signal
  coverage. It keeps `live_money_orders_enabled=false`.
- `scripts/pi4_soak.sh`: repeatable non-mutating Pi4 profile loop built on
  `scripts/pi4_rc_profile.sh`. A long-running soak still needs fresh wall-clock
  runtime evidence from the target device.
- `final-smoke.txt`: 2026-06-28 `bash scripts/final_smoke.sh` exited `0`,
  including Docker install, `/api/v1/ping`, auth denial, authenticated
  dashboard/home fetch, safe uninstall, and purge uninstall.
- `pi4-ssh-probe.txt`: 2026-06-28 key-based SSH probe reached the Pi and
  captured `temp=49.6'C`, `throttled=0xe0000`.
- `final-gate/pytest.txt`: 2026-06-28 full test suite `575 passed`.
- `final-gate/release-wording-scan-final.txt`: `violations=0`.
- `final-smoke-latest.txt`: 2026-06-28 fresh Docker final smoke exited
  `0` after freeing the local UI port; it reached install, authenticated
  ping/home fetch, safe uninstall, and purge uninstall.
- `wp3/api-dashboard-readmodels.txt`: authenticated API/dashboard read models
  expose balance, open/closed PnL, W/L, exposure, reconciliation status, and
  safety signals without adding write endpoints.
- `wp3/runtime-health.txt`: CLI/API runtime health returns stable machine codes
  for heartbeat, preflight, database, wallet freshness, market data freshness,
  reconciliation age, exchange API errors, circuit breaker state, disk, and
  memory.
- `wp3/pi4-soak.md`: `scripts/pi4_soak.sh` records bounded CPU/profile,
  memory/load, temp/throttle, runtime-health, and testnet-pilot outputs while
  staying non-mutating and secret-safe. The local run recorded WSL/Docker/Pi
  environment blockers rather than public Pi4 performance proof.
- `wp4/final-smoke.md`: strict gates passed (`ruff`, `basedpyright`,
  `uv run pytest -q` with 621 passed, release wording scan with zero
  violations, and `git diff --check`). `bash scripts/final_smoke.sh` passed its
  pre-Docker sections and then recorded `INSTALL_DOCKER_UNAVAILABLE` because
  Docker is not installed in the current WSL distro. Browser smoke is also
  blocked locally by missing Chromium `libnspr4.so`.
- `wp5/live-canary-manual-evidence.md`: live canary execution is
  `blocked-no-live-credentials`; no real-money order was placed and no WP6 live
  runtime approval was created.
- `wp6/restricted-live-pilot-tests.txt`: restricted live pilot startup guards are
  implemented and report `LIVE_PILOT` blocked without a sanitized canary-pass
  marker.
- `wp6/live-24h-soak.md`: restricted live 24h soak is
  `blocked-awaiting-owner-live-approval`; no live pilot ran and release status
  remains canary-ready implementation only.


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
  re-verified in G011, and the 2026-06-28 final smoke rechecked shell
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
  stable sample client order id, a closed order-state list, and dashboard safety
  signal coverage. It does not submit exchange orders.
- The home operator surface now shows the six live-execution safety signals
  required before any separate live-order pilot can be approved.
- Backend dashboard/API read models now expose account truth for balance,
  open/closed PnL, W/L, exposure, reconciliation status, execution lifecycle,
  and safety signals as protected read-only surfaces.
- Runtime-health CLI/API now reports stable machine codes for heartbeat,
  preflight, database readability/writability, wallet freshness, data
  freshness, reconciliation age, exchange API error counters, breaker state,
  disk budget, and memory budget.
- Live canary preview and order-lane code now require an explicit preview hash,
  owner confirmation phrase, fixed notional, fixed reference price, ledger
  idempotency, immediate reduce-only exit, and reconciliation event recording.
  This path is fake-client proven only; no real live canary has been run.
- Restricted live pilot startup guards now exist as a runtime-health/control
  blocker: without a sanitized live-canary pass marker, explicit stake/leverage,
  fresh reconciliation and wallet timestamps, enabled breakers, and manual halt
  path, runtime health reports `LIVE_PILOT` blocked and runtime control refuses
  new entries. No restricted live pilot has run.
- The 2026-07 next-phase review froze the publish boundary, rechecked account
  truth/dashboard/runtime-health surfaces, and prepared a live-gate decision
  packet without executing live orders or creating a canary-pass marker.
- Fresh 2026-07 local continuation gates passed: strict Python quality gates,
  full pytest, frontend typecheck/build, plan-evidence verification,
  release-wording scan, and final smoke including Docker install, ping, auth
  denial, authenticated home/dashboard fetch, safe uninstall, and purge.

## Partial

- Pi4 is an internal RC lane for the measured hardware. Historical 2026-06 Pi4
  receipts remain preserved, but the fresh connected-Pi4 WP8 revalidation is
  blocked by `PI4_THROTTLED` and `PI4_UV_MISSING`; no public current-Pi4 pass or
  performance claim is supported.
- The update button is proof-only: preview/apply/rollback receipts exist, but
  automatic GitHub source mutation remains outside this RC.
- Exchange support is capability/evidence promoted. Candidate and
  generic-unverified exchanges remain blocked from runtime trade paths until
  fixture, sandbox, or testnet evidence promotes them.
- Binance is the owner-primary deep-validation lane. Registered non-Binance
  exchange modes keep deterministic fixture/sandbox/report-only runtime
  evidence and are expanded through safe keys or redacted user issue reports.
- The dashboard/API account-truth model is now backend-owned and protected.
  Frontend layout refinement remains separate; the current proof is correctness,
  bounded payloads, redaction, and read-only status rather than a redesign.
- Pi4 soak automation is present and captures bounded profile/resource/runtime
  outputs, but multi-hour or multi-day target-hardware evidence must still be
  captured before any public Pi4 performance statement.

## Blocked Or Not Done

- Real-money live order approval remains blocked: WP5.3 recorded
  `blocked-no-live-credentials`, WP6.2 recorded
  `blocked-awaiting-owner-live-approval`, and WP11 created a decision packet only.
  Restricted live pilot runtime cannot run until owner-approved live-canary
  execution, sanitized reconciliation, immediate exit/reduce-only proof, wallet
  before/after proof, rollback evidence, and an explicit canary-pass marker
  exist.
- Blocked: public Freqtrade superiority, profit, safety guarantee, upstream X7
  trade parity, and public Pi4 performance comparison claims.
- Real exchange credentials must be re-entered by the operator in local runtime
  secret storage; they are not recoverable from sanitized RC evidence.
- Real Binance testnet credential checks are blocked until safe testnet keys are
  supplied through local secret storage. Bybit, OKX, and Bitget stay as
  template/issue-driven expansion lanes until safe keys or user reports exist.
- Multi-OS install/uninstall repetition beyond the current matrix still needs
  more evidence.

## Publication Boundary

- README and release notes may say paper/testnet RC, native NFI-shaped X7
  runtime, evidence-backed deterministic exchange lanes, protected account-truth
  read models, runtime-health machine checks, and final-smoke evidence. Fresh
  environment blockers must be stated plainly when cited.
- README and release notes must not say live-money ready, profit-capable,
  guaranteed safe, comparative superiority, full upstream X7 trade parity, all
  exchanges fully supported, public Pi4 performance proven, or browser/manual QA
  passed unless fresh evidence is cited.
- Live-execution work remains limited to separately approved canary/restricted
  pilot gates. Current WP5/WP6 evidence proves the guarded implementation and the
  honest live-runtime blocker; it does not unlock real-money orders.
