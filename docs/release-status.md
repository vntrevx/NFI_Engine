# Release Status

Date: 2026-06-24 KST
Current review note: 2026-06-24 KST

This document is the current status summary for the evidence-backed
paper/testnet release-candidate lane. It is not approval for real-money live
order execution.

## Verdict

The RC lane is approved for paper/testnet evaluation within the documented
safety boundary, based on the captured evidence root below. The latest
2026-06-24 documentation review adds G072 browser evidence: language and runtime
state update without forced refresh, auth/CSRF/read-only/live-intent probes stay
blocked, and KO/EN/EL desktop/mobile visual QA has no overflow. A 2026-06-23
fresh rerun of the full Docker smoke was blocked by host state because Docker
was unavailable in that WSL session and Docker Desktop was not reachable. That
rerun blocker is not treated as a product pass.

```text
.omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/
```

Final local gates under that root include:

- `f1-plan-compliance.md`: Todos 1-14 covered, plan evidence verified.
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
- One-line shell, npm, and Bun install/uninstall paths were re-verified in G011:
  `.omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/ulw-reconcile-g011/`.
- Pi4 RC checks include user-home toolchain staging, benchmark budget
  resolution, 500-tick X7 paper soak, loopback deployment profile, stock-host
  rollback receipts, no throttling in the captured runs, and G063 revalidation
  of the non-mutating `pi4_rc_profile` edge path.
- Release wording policy blocks unsupported claims and the deterministic scan
  currently reports zero violations.

## Partial

- Pi4 is an internal RC lane for the measured hardware. It is not a public speed
  comparison claim, and cooling UX still needs a new heatsink/fan measurement.
- The update button is proof-only: preview/apply/rollback receipts exist, but
  automatic GitHub source mutation remains outside this RC.
- Exchange support is capability/evidence promoted. Candidate and
  generic-unverified exchanges remain blocked from runtime trade paths until
  fixture, sandbox, or testnet evidence promotes them.
- The dashboard is usable as an operator cockpit, but richer position, account,
  PnL, and risk compression still belongs to later work.

## Blocked Or Not Done

- Real-money live order execution remains blocked pending a separate approved
  live-execution plan.
- Blocked: public Freqtrade superiority, profit, safety guarantee, upstream X7
  trade parity, and public Pi4 performance comparison claims.
- Real exchange credentials must be re-entered by the operator in local runtime
  secret storage; they are not recoverable from sanitized RC evidence.
- Fresh Docker final smoke rerun is blocked until Docker Desktop/WSL
  integration is available again. Prior isolated Docker proof remains evidence,
  but fresh release claims should rerun `bash scripts/final_smoke.sh`.
- Multi-OS install/uninstall repetition beyond the current matrix still needs
  more evidence.

## Next Work

1. Complete G074 full quality gate or name only pre-existing unrelated blockers
   with exact evidence.
2. Start a separate live-execution design only after the RC is reviewed.
3. Add richer dashboard account/position/risk compression for repeated operator
   use.
4. Re-run Pi4 long-run thermal evidence after the cooling hardware is changed.
5. Promote exchanges from candidate to verified only through fixture,
   sandbox, or testnet evidence.
