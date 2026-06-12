# Performance

M2 starts with local baseline evidence. It does not publish relative speed
claims against Freqtrade. Public comparison claims require same-machine,
same-workload, black-box benchmark evidence and a report that says the claim is
allowed.

## Run The M2 Benchmark

```bash
bash scripts/benchmark_m2.sh
python3 -m json.tool .omo/evidence/m2-benchmark.json
```

The wrapper calls:

```bash
uv run nfi-engine benchmark m2 --output .omo/evidence/m2-benchmark.json
```

The benchmark writes machine metadata, workload labels, measured durations, local
budgets, and an optional Freqtrade comparison object. Normal contributor runs do
not need Freqtrade installed.

## Current M2 Surfaces

- `startup_smoke`: creates the FastAPI app with a static dashboard read store.
- `dashboard_snapshot_latency`: builds and serializes the dashboard snapshot contract from empty fixture read models.
- `home_render_smoke`: renders the local Home HTML.
- `chart_render_smoke`: renders the dashboard chart shell without a heavy chart dependency.
- `install_smoke`: generates setup config in a temporary runtime directory and validates it.

These are baseline checks, not tuning proof. If a measurement exceeds its local
budget, the report marks it as `warn` so maintainers can decide whether to
optimize or update the budget with evidence.

## Release Smoke Gate

The final local release smoke includes the benchmark wrapper:

```bash
bash scripts/final_smoke.sh
```

That command must write a valid `.omo/evidence/m2-benchmark.json`, but it does
not claim a regression gate unless a previous report is supplied through
`--baseline`. The 2026-06-12 dev-entry evidence keeps the release-gate artifacts
under `.omo/evidence/2026-06-12-dev-entry/task-7-final-smoke/`, including the
successful smoke log, generated benchmark JSON, browser screenshots, redacted
HAR files, and the explicit regression-failure transcript.

## Regression Gate

Compare against an older JSON report:

```bash
uv run nfi-engine benchmark m2 --output .omo/evidence/m2-benchmark.json --baseline .omo/evidence/old-m2-benchmark.json
```

A measurement more than 5 percent slower than the baseline fails with
`PERFORMANCE_REGRESSION`. Temporary acceptance requires both:

```bash
uv run nfi-engine benchmark m2 --output .omo/evidence/m2-benchmark.json --baseline .omo/evidence/old-m2-benchmark.json --allow-regression --regression-reason "documented reason"
```

Use that only when the slower result is intentional and tracked.

## Optional Freqtrade Comparison Fields

The JSON schema includes:

- `freqtrade_available`
- `freqtrade_version`
- `workflow`
- `nfi_engine_result`
- `freqtrade_result`
- `ratio`
- `claim_allowed`

M2 sets `freqtrade_available=false` and `claim_allowed=false`. Later comparison
jobs should fill these fields only through black-box CLI/API workflows against a
pinned Freqtrade version or container.
