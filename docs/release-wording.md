# Release Wording Guardrails

## Scope

This policy defines what can be stated in NFI Engine public documentation and release communication.
The goal is to keep claims evidence-bound, safe, and aligned with the clean-room
compatibility boundary.

## Allowed phrasing

The following phrases are allowed when they describe what is actually implemented and
supported, and when backed by local evidence:

- `native NFI-shaped X7 runtime`
- `dry-run/paper/testnet path`
- `local evidence-backed benchmark`
- `clean-room compatibility boundary`
- `Freqtrade-shaped callbacks` when referring only to callback names and adapter contracts.

Allowed phrasing should stay implementation- or process-oriented and avoid guarantees.

## Blocked phrasing (do not publish as-is)

Unless a direct exception exists in a release ticket and dedicated evidence is attached,
the following language is blocked:

- guaranteed profit
- profit promise
- guaranteed safety / safety guarantee
- full NFI X7 trade parity
- 100% parity
- superior / better than Freqtrade
- live-money ready
- 100% complete
- Pi4 public performance claims without hardware-stamped benchmark evidence
- Korean equivalents such as `Freqtrade보다 우월`, `수익 보장`, `안전 보장`,
  `완전 패리티`, `실거래 준비 완료`, and `100% 완료`.

## Evidence rule for public claims

Any public claim that uses benchmarks, compatibility, runtime, performance, or safety
positioning must link to evidence generated in:

- `.omo/evidence/...`
- `.omo/ulw-loop/evidence/...`

Each claim in release notes, README, and docs should include:

1. The artifact path.
2. The producer command or process.
3. A date stamp and dataset/config/build scope.

If a claim has no matching artifact, treat it as blocked and rewrite to a neutral
statement (for example: "implemented", "under development", "planned", or
"measured in local smoke").

## Current RC wording boundary

As of 2026-06-26, the evidence-backed public boundary is:

- The project has a native NFI-shaped X7 paper/testnet release-candidate lane.
- The current RC evidence root is
  `.omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/`.
- The current final-publication evidence root is
  `.omo/evidence/2026-06-26-nfi-engine-final-product-publication/`.
- The 2026-06-26 Docker final smoke may be described as a fresh local
  release-smoke pass when the statement names the T6 evidence artifact.
- The Pi4 evidence may be described as measured internal RC evidence for one
  Raspberry Pi 4 device, with `claim_allowed=false`; the 2026-06-26 probe was
  cool and reachable but retained historical throttle flags, so it is not a
  public performance claim.
- The G072 UI evidence may be described as local browser QA for no-forced-refresh
  language/runtime updates, protected browser/API paths, and desktop/mobile
  KO/EN/EL visual checks.
- Real priority-exchange testnet credentials were not present in T8; wording may
  say the lane is `blocked-no-key`, not that real testnet balances/orders were
  validated.
- Real-money live order execution remains blocked pending a separate approved
  plan and evidence set.

Avoid wording that turns the Pi4 benchmark into a public comparison, guarantee,
or money outcome statement.

## Documentation check before publishing

- For each doc sentence using a protected phrase, verify the referenced evidence exists
  before merge.
- Avoid absolute performance, parity, and money outcome wording in examples unless evidence
  is attached at the sentence level.
- Keep public-facing language concrete, minimal, and reproducible.
- Do not reuse upstream prose from Freqtrade or NFI strategy internals for marketing or
  release phrasing.

## Deterministic wording scan

Run the local scan before publishing README or docs changes:

```bash
uv run python scripts/release_wording_scan.py
```

The scan must print `violations=0`. Controlled negative tests should use a
temporary file and should not edit public docs just to prove the failure path.
