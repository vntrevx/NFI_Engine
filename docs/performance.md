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
- `backtest_720_candle_latency`: runs a deterministic 720-candle clean-room backtest workload.
- `x7_strategy_inspect_latency`: inspects native X7 callbacks and the semantic coverage ledger.
- `x7_feature_graph_latency`: builds the native X7 feature graph from synthetic OHLCV and informative frames.
- `x7_backtest_sample_latency`: runs a bounded native X7 backtest sample without Freqtrade runtime imports.
- `x7_paper_sample_latency`: runs a bounded native X7 paper sample with temporary SQLite and no live orders.
- `install_smoke`: generates setup config in a temporary runtime directory and validates it.

These are baseline checks, not tuning proof. If a measurement exceeds its local
budget, the report marks it as `warn` so maintainers can decide whether to
optimize or update the budget with evidence.
Raspberry Pi 4 wording needs a benchmark report captured on Pi hardware; local
x86_64 or CI runs are only same-machine regression evidence.

## Current X7 Semantic-Port Baseline

The 2026-06-20 Todo 15 run is workstation evidence only:

```bash
uv run nfi-engine benchmark m2 --config examples/futures-paper.yaml --samples 5 --output .omo/evidence/2026-06-20-nfi-x7-semantic-port/task-15-benchmark.json
```

All ten measurements passed their local budgets on WSL2 x86_64:

| Measurement | Samples | Result ms | Budget ms | Payload bytes |
| --- | ---: | ---: | ---: | ---: |
| `startup_smoke` | 5 | 123.740 | 1000.0 | 54 |
| `dashboard_snapshot_latency` | 5 | 0.121 | 50.0 | 2391 |
| `home_render_smoke` | 5 | 0.323 | 50.0 | 33733 |
| `chart_render_smoke` | 5 | 0.003 | 5.0 | 793 |
| `backtest_720_candle_latency` | 5 | 11.898 | 1000.0 | 720 |
| `x7_strategy_inspect_latency` | 5 | 0.200 | 50.0 | n/a |
| `x7_feature_graph_latency` | 5 | 20.352 | 100.0 | n/a |
| `x7_backtest_sample_latency` | 5 | 545.303 | 1000.0 | n/a |
| `x7_paper_sample_latency` | 5 | 197.530 | 1000.0 | n/a |
| `install_smoke` | 5 | 4.007 | 1000.0 | 654 |

This locks a local regression baseline for the native X7 strategy surface:
strategy inspect, feature graph, backtest sample, and paper sample. It does not
publish a Raspberry Pi 4 claim or a Freqtrade comparison claim; the report keeps
`claim_allowed=false`.

## Current Raspberry Pi 4 X7 RC Baseline

The 2026-06-22 T5A run is actual Raspberry Pi 4 hardware evidence for the
native X7 M2 surface after feature-row allocation tuning:

```bash
uv run nfi-engine benchmark m2 --config examples/x7-futures-paper.yaml --samples 3 --output /tmp/nfi-x7-m2-pi4-final1.json
```

Hardware and runtime:

- Raspberry Pi 4 Model B Rev 1.5
- Debian Raspberry Pi OS aarch64, kernel `6.12.75+rpt-rpi-v8`
- Python 3.13.5 via the staged Pi user-home toolchain
- CPU max frequency `1800000` KHz
- `vcgencmd get_throttled`: `throttled=0x0`
- Temperature snapshot after evidence capture: `53.5C`
- `claim_allowed=false`

The repeated same-Pi runs resolved the previous `x7_backtest_sample_latency`
warning without increasing the 1000 ms budget:

| Evidence file | Samples | `x7_feature_graph_latency` ms | `x7_backtest_sample_latency` ms | Budget ms | Status |
| --- | ---: | ---: | ---: | ---: | --- |
| `task-05a-pi4-x7-backtest-budget/nfi-x7-m2-pi4-final1.json` | 3 | 20.706 | 832.086 | 1000.0 | pass |
| `task-05a-pi4-x7-backtest-budget/nfi-x7-m2-pi4-final2.json` | 3 | 20.241 | 836.042 | 1000.0 | pass |
| `task-05a-pi4-x7-backtest-budget/nfi-x7-m2-pi4-final3.json` | 3 | 17.688 | 849.583 | 1000.0 | pass |

Failure proof is also captured: an impossible X7 baseline fails with
`PERFORMANCE_REGRESSION` instead of silently passing. This is an internal Pi4
RC budget result, not a public speed claim against Freqtrade.

## Current T15 Baseline

The 2026-06-16 T15 run is workstation evidence only:

```bash
uv run nfi-engine benchmark m2 --config examples/futures-paper.yaml --samples 5 --output .omo/evidence/2026-06-16-product-completion/task-15-benchmark.json
```

All six measurements passed their local budgets on WSL2 x86_64:

| Measurement | Samples | Result ms | Budget ms | Payload bytes |
| --- | ---: | ---: | ---: | ---: |
| `startup_smoke` | 5 | 176.808 | 1000.0 | 48 |
| `dashboard_snapshot_latency` | 5 | 0.285 | 50.0 | 2391 |
| `home_render_smoke` | 5 | 0.550 | 50.0 | 31693 |
| `chart_render_smoke` | 5 | 0.005 | 5.0 | 793 |
| `backtest_720_candle_latency` | 5 | 10.374 | 1000.0 | 720 |
| `install_smoke` | 5 | 5.147 | 1000.0 | 654 |

Pi4 claim blocked: these numbers do not prove Raspberry Pi 4 performance. They
only lock a local no-regression baseline until the same command is run on actual
Pi4 hardware and the report is stored with machine metadata.

## Current Raspberry Pi 4 Tuned Baseline

The 2026-06-16 Pi4 tuned run is actual Raspberry Pi 4 hardware evidence:

```bash
uv run nfi-engine benchmark m2 --config examples/futures-paper.yaml --samples 5 --output .omo/evidence/2026-06-16-pi4/m2-benchmark-after-tuning.json
```

Hardware and runtime:

- Raspberry Pi 4 Model B Rev 1.5
- Debian GNU/Linux 13 `trixie`, aarch64
- Python 3.12.13 via `uv`
- 4 CPU cores, 3.7Gi RAM, USB root disk at `/dev/sda2`
- `vcgencmd get_throttled`: `throttled=0x0`
- Pi4 deployment is on hold. After the hold decision, Pi-specific NFI tuning was
  removed from the host:
  - `nfi-engine-pi4-performance.service`: removed
  - `nfi-engine-pi4-quiet-cpufreq.service`: removed
  - `nfi-engine-thermal-guard.service`: removed
  - current governor after reboot: `ondemand`
  - CPU max remains uncapped at `1800000` KHz
- Pi-specific sysctl, journald, Docker daemon log-policy, Bluetooth disable, and
  GPIO fan boot overlays were removed. The post-cleanup boot config only keeps
  the stock `enable_uart=1` line from this investigation.
  Post-cleanup sysctl values are back to common defaults such as
  `vm.swappiness=60`, `vm.dirty_background_ratio=10`, and `vm.dirty_ratio=20`.

Pi4 deployment status: hold. The engine is verified on the measured Pi4, but
the current two-wire 5V fan is too loud for acceptable operator UX. Treat Pi4
as a proven lab target, not the recommended always-on deployment target, until
cooling is changed to one of:

- fan removed with heatsink-only monitoring and thermal guard enabled
- low-noise 5V fan
- GPIO/PWM-controllable fan or MOSFET fan controller

## Raspberry Pi 4 RC Deployment Profile

The 2026-06-22 RC profile keeps the Pi host stock by default. It does not
install services, lower CPU max frequency, touch boot files, disable Bluetooth,
change sysctl/journald/Docker daemon settings, or assume a fan controller:

```bash
bash scripts/pi4_rc_profile.sh --project-name nfi-engine-pi4-rc --host-port 18113 --output .omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/task-13-pi4-deploy/pi4-rc-profile.txt
bash scripts/install.sh --yes --paper --testnet --project-name nfi-engine-pi4-rc --host-port 18113
bash scripts/uninstall.sh --yes --project-name nfi-engine-pi4-rc
```

The profile is a deployment gate, not an optimization toggle. It blocks on
reduced CPU max frequency, active throttling, high temperature, missing
runtime tools, public Compose binding, unbounded Docker logs, or low disk
space. Passing it means the RC stack is conservative and reversible on that
machine; it still does not prove live-money readiness or public speed claims.

All six performance-restored measurements passed their local budgets on Pi4:

| Measurement | Samples | Result ms | Budget ms | Payload bytes |
| --- | ---: | ---: | ---: | ---: |
| `startup_smoke` | 5 | 471.405 | 1000.0 | 48 |
| `dashboard_snapshot_latency` | 5 | 0.385 | 50.0 | 2391 |
| `home_render_smoke` | 5 | 1.095 | 50.0 | 31693 |
| `chart_render_smoke` | 5 | 0.011 | 5.0 | 793 |
| `backtest_720_candle_latency` | 5 | 39.013 | 1000.0 | 720 |
| `install_smoke` | 5 | 12.633 | 1000.0 | 654 |

Compared with the first untuned Pi4 run from the same device, the current
performance-restored run remains faster across every M2 surface. The largest
movement is `startup_smoke` (`763.939ms` to `471.405ms`). A previous
performance-governor run reached `424.967ms`; keep both reports as
same-device regression evidence rather than portable speed claims.

Thread comparison also passed for `POLARS_MAX_THREADS=1`, `2`, and `4`; the
4-thread run was marginally fastest for the deterministic 720-candle backtest.
No forced Polars thread cap is applied by default because the stock 4-core
setting is already within budget and keeps the backtest path fastest.

This Pi4 baseline supports low-resource regression tracking for NFI Engine on
the measured hardware. It still does not support public speed claims against
Freqtrade because `claim_allowed=false` and no same-machine black-box Freqtrade
comparison was run.

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
