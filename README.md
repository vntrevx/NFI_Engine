# NFI Engine

[English](README.md) | [한국어](README.ko.md)

NFI Engine is an original, clean-room crypto trading engine for spot/futures
paper trading, testnet-oriented operator workflows, deterministic simulation,
and native NFI-shaped X7 strategy research.

It is not Freqtrade, not an official NostalgiaForInfinity project, and not a
fork of either codebase. Freqtrade is used only as a feature benchmark for the
kind of operating surface a serious engine should cover. Upstream NFI strategy
code is not vendored or runtime-imported by this repository.

## Current Status

As of 2026-06-24 KST, the project is an evidence-backed paper/testnet release
candidate. It is not a real-money live-order release.

| Area | Current boundary |
| --- | --- |
| Strategy runtime | Native NFI-shaped X7 semantic runtime is available for dry-run, paper, and testnet-oriented paths. |
| Operator flow | One-line install/uninstall, token login, Home cockpit, Settings setup, wallet balance fetch, runtime controls, logs, and EN/KO/EL UI are implemented. |
| Safety | Auth, CSRF, read-only mode, live-intent blockers, preflight, wallet caps, reconciliation, circuit breakers, and update rollback gates stay enforced. |
| Exchange support | Exchanges are promoted by capability evidence. Candidate and generic-unverified exchanges do not enter runtime trade paths. |
| Raspberry Pi 4 | Internal RC evidence exists for one measured Pi4 lane, with `claim_allowed=false`; it is not a public speed comparison. |
| Live execution | Real-money live order execution remains blocked pending a separate approved design and evidence set. |

The current status summary is maintained in
[docs/release-status.md](docs/release-status.md). Public wording is governed by
[docs/release-wording.md](docs/release-wording.md).

## Product Shape

NFI Engine is designed as a local operator console first: fewer decisions,
explicit safety explanations, typed runtime boundaries, reproducible evidence,
and small modules that can be maintained on low-resource hardware. The current
product lane includes:

- guided setup for exchange API credentials, permission audit, recommended 3x leverage, explicit wallet balance fetch, allocation, spot/futures, and dry-run/live intent;
- Home cockpit for runtime state, readiness, risk, wallet, chart snapshots, pairlist, recent errors, and safe controls;
- Settings and Logs pages with local-only browser behavior, no CDN assets, no browser token storage, and redacted support output;
- clean-room X7 inspection and paper/testnet signal runtime without copying upstream strategy source;
- one-line shell, npm, and Bun install/uninstall wrappers;
- deterministic docs, release wording, benchmark, browser QA, and quality gates.

See [docs/freqtrade-feature-coverage.md](docs/freqtrade-feature-coverage.md) for
the clean-room feature map and NFI Engine differentiation rules. X7 runtime
boundaries live in [docs/nfi-x7-compatibility.md](docs/nfi-x7-compatibility.md),
and exchange status lives in
[docs/exchange-support-matrix.md](docs/exchange-support-matrix.md).

## Quickstart

Docker is the primary first-run path. From a local checkout:

```bash
bash scripts/install.sh --yes --paper --testnet
```

The same one-line installer is exposed through npm and Bun wrappers for
operators who prefer a package-manager command:

```bash
npm run nfi:install
bun run nfi:install
```

Dry-run receipts are available before starting Docker:

```bash
bash scripts/install.sh --yes --paper --testnet --dry-run
npm run nfi:install:dry-run
bun run nfi:install:dry-run
```

First Run:

1. Open `http://127.0.0.1:18080/`.
2. Paste the local operator token from `.runtime/docker.env` into the login screen. The installer prints `login_token_file=.runtime/docker.env`, never the token value.
3. Use Home to check the operator cockpit, Setup Doctor, Safety Explainer, chart status, runtime controls, recent errors, and pairlist state.
4. Use Settings for first-run setup: exchange, exchange API key, exchange API secret, API permission audit, recommended 3x leverage, risk profile, explicit wallet balance fetch, allocated amount, futures/spot, and dry-run/live.
5. Keep dry-run selected unless the live confirmation path is intentionally being tested. Withdrawal-like API permission blocks live setup, expert risk requires explicit confirmation, and API key/secret fields are write-only and redacted from output.
6. Use the language selector for English, Korean, and Greek UI text.
7. Use Logs to export a redacted support report when an error code appears.

Useful first checks:

```bash
curl -i http://127.0.0.1:18080/api/v1/ping
bash scripts/uninstall.sh --yes
npm run nfi:uninstall
bun run nfi:uninstall
```

Native X7 semantic-runtime inspection is available on the dry-run/paper/testnet
path without vendoring upstream strategy code:

```bash
uv run nfi-engine strategy inspect --config examples/x7-futures-paper.yaml --strategy nfi_engine.strategy.nfi_x7:X7NativeStrategy --json
```

Safe uninstall preserves generated runtime files and data volumes. Destructive
purge is explicit; npm and Bun expose only the purge preview:

```bash
bash scripts/uninstall.sh --purge --yes
npm run nfi:uninstall:purge:dry-run
bun run nfi:uninstall:purge:dry-run
```

Do not enter real exchange credentials into issues, chat logs, committed files,
or shell history. For local setup, prefer testnet or paper credentials and rotate
them after experiments.

## Developer Setup

Use the manual path when developing the engine without Docker:

```bash
uv sync
uv run nfi-engine --help
uv run nfi-engine config validate --config examples/spot-paper.yaml
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml
uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/quickstart-backtest.json
uv run nfi-engine serve --config examples/futures-paper.yaml --host 127.0.0.1 --port 18080
```

Open:

- `http://127.0.0.1:18080/`
- `http://127.0.0.1:18080/settings`
- `http://127.0.0.1:18080/logs`

When `api.auth_token` is configured, create a browser session through the login
screen before using protected pages. Mutating API calls require the session
cookie and `x-nfi-csrf-token`; the token is never stored in browser local
storage.

## Docker Quickstart

```bash
bash scripts/install.sh --yes --paper --testnet
npm run nfi:install
bun run nfi:install
curl -i http://127.0.0.1:18080/api/v1/ping
bash scripts/uninstall.sh --yes
```

Compose binds the API to `127.0.0.1:18080` by default and uses named volumes for
data and logs. Safe uninstall preserves generated runtime files and named
volumes; `bash scripts/uninstall.sh --purge --yes` removes them. Do not put
exchange secrets in committed env files. See [docs/docker.md](docs/docker.md).

## Why NFI Engine Is Different

NFI Engine borrows feature pressure from mature trading bots, then reshapes the
operator experience around fewer decisions, explicit safety gates, benchmark
evidence, and small module boundaries. The goal is not to imitate FreqUI or
publish speed claims early. The goal is a maintainable engine where setup,
diagnostics, strategy research, and performance work are easy to verify.

## Architecture Map

- `src/nfi_engine/config`: Pydantic runtime settings, metadata, migration, and redaction.
- `src/nfi_engine/domain`: branded market, pair, order, and trading-mode value objects.
- `src/nfi_engine/strategy`: clean adapter contract for Freqtrade-shaped strategies.
- `src/nfi_engine/backtest`: deterministic backtest runner and reproducibility metadata.
- `src/nfi_engine/validation`: walk-forward validation and split serialization.
- `src/nfi_engine/paper`: paper-run lifecycle and tick-driven state transitions.
- `src/nfi_engine/exchange`: exchange adapters, fixtures, reconciliation, and fill scenarios.
- `src/nfi_engine/risk`, `orders`, `circuit_breakers`, `safety`: risk decisions and hard stops.
- `src/nfi_engine/persistence`, `maintenance`: SQLite storage, migrations, backups, restore.
- `src/nfi_engine/plugins`, `sandbox`: plugin registry and strategy import policy.
- `src/nfi_engine/notifications`, `observability`: operator events, logs, notifiers, reports.
- `src/nfi_engine/api`, `ui`: FastAPI REST/WebSocket API and local operator console.

Module boundaries are intentionally narrow. Config parsing happens at the edge,
domain services receive typed values, and UI actions call typed API endpoints
instead of editing raw YAML.

## Core Commands

```bash
uv run nfi-engine profile list
uv run nfi-engine config show --config examples/futures-paper.yaml
uv run nfi-engine config schema --config examples/futures-paper.yaml
uv run nfi-engine validate walk-forward --config examples/spot-paper.yaml --splits 3 --output .omo/evidence/walk-forward.json
uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 25
uv run nfi-engine plugins list --config examples/futures-paper.yaml
uv run nfi-engine circuit-breaker simulate --config tests/fixtures/config/daily-loss-limit.yaml
uv run nfi-engine notify test --config examples/futures-paper.yaml --channel jsonl --message smoke --output .omo/evidence/notify.jsonl
uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.nfi_shape:NFISmokeStrategy
```

## Operations

Start with a profile and preflight check before any paper run:

```bash
uv run nfi-engine profile list
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml
```

Maintenance commands are dry-run first:

```bash
uv run nfi-engine db migrate --dry-run --database tests/fixtures/db/v0.sqlite
uv run nfi-engine config migrate --dry-run --config tests/fixtures/config/v0-config.yaml
uv run nfi-engine config history --config examples/futures-paper.yaml
uv run nfi-engine backup create --config examples/futures-paper.yaml --output .omo/evidence/backup.zip
uv run nfi-engine backup verify .omo/evidence/backup.zip
uv run nfi-engine backup restore --dry-run .omo/evidence/backup.zip
```

Exchange and market checks:

```bash
uv run nfi-engine exchange capabilities --exchange bybit --trading-mode futures --format json
uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_match.json
uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/pairlist.json
uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/fill-sim.json
```

`exchange capabilities` labels registry profiles and report-only generic ids
without promoting unknown exchanges into config, paper/testnet, or live paths.

See [docs/operations.md](docs/operations.md), [docs/backup.md](docs/backup.md),
[docs/reconciliation.md](docs/reconciliation.md), [docs/pairlist.md](docs/pairlist.md),
and [docs/simulator.md](docs/simulator.md).

## Frontend Console

The console is a local operator surface, not a public dashboard.

- `/`: Home cockpit with setup readiness, runtime health, pause/resume/stop-safe controls, wallet balance state, action queue, local chart, safety, and support shortcuts.
- `/settings`: first-run setup wizard, config metadata editor, validation, draft/apply, readiness, pairlist, update states, safety locks.
- first-run setup wizard: exchange credentials, API permission audit, 3x recommendation, risk profile, explicit wallet balance fetch, amount, futures/spot, dry-run/live, redacted preview.
- update state panel: local-safe preview/apply/rollback states for future engine+strategy update flow.
- `/logs`: recent logs, severity filter, error-code lookup, correlation IDs, support report export.
- Read-only mode: settings/logs/pairlists are inspectable, while save/apply/restore/start/pause/resume/stop are disabled and server-blocked.
- Security: authenticated session cookie, CSRF token for mutations, protected wallet fetch and runtime health JSON, logout, expiry, protected audit log, no browser token storage.

See [docs/ui.md](docs/ui.md).

## Feature Coverage

Freqtrade remains the functional benchmark, but NFI Engine must stay original in
design and implementation. Each broad feature category is tracked with an
explicit NFI Engine angle in
[docs/freqtrade-feature-coverage.md](docs/freqtrade-feature-coverage.md).
The clean-room NFI X7 target facts live in
[docs/nfi-x7-compatibility.md](docs/nfi-x7-compatibility.md), while exchange
support is separated into `candidate`, `verified`, and `generic-unverified`
levels in [docs/exchange-support-matrix.md](docs/exchange-support-matrix.md).

## Evidence And Quality Gates

Use the smoke harness to refresh final evidence files:

```bash
bash scripts/final_smoke.sh
uv run python scripts/release_wording_scan.py
```

The current operator and X7 semantic-runtime evidence roots are:

```text
.omo/evidence/2026-06-12-dev-entry/
.omo/evidence/2026-06-20-nfi-x7-semantic-port/
.omo/evidence/2026-06-21-x7-live-readiness-pi4-rc/
```

The 2026-06-21/22 RC root is the current paper/testnet release-candidate lane.
It records X7 semantic inspection, exchange/wallet gates, order-lifecycle
testnet boundaries, runtime-control safety, browser workflow evidence, update
rollback proof, Pi4 install/soak/deploy receipts, and the T5A Pi4 X7 benchmark
budget resolution. The Pi4 evidence keeps `claim_allowed=false`; use it for
internal RC gating, not public speed or live-money wording.

The current dated status summary is maintained in
[docs/release-status.md](docs/release-status.md). It separates completed,
partial, blocked, and next work for the current RC lane.

The release gate includes Docker install/login/Home smoke, local benchmark JSON,
a supplied-baseline regression failure check, install/uninstall dry-run receipts,
package-wrapper bootstrap smoke, and desktop/mobile browser
evidence for Home, Settings, Logs, the login path, X7 strategy inspection, and
the deterministic release-wording scan. Benchmark regression blocking only
applies when `--baseline` is supplied; first-run smoke validates the generated
local report without claiming public speed superiority.

Focused live-server browser QA:

```bash
npm install
npm run nfi:browser-qa:deps
npm run nfi:browser-qa
```

This starts a QA-only loopback server, logs in through the real browser page,
switches Settings locale without manual F5, captures Home/Settings/Logs
desktop and mobile screenshots, and fails on external network requests or
browser token storage.

Core quality gate:

```bash
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest -q
```

Scripted quality gate:

```bash
bash scripts/quality_gate.sh --docs-only
bash scripts/quality_gate.sh --strict
bash scripts/quality_gate.sh --coverage-only
```

`--docs-only` is the fast default for governance and documentation edits.
`--strict` runs the full local gate above. `--coverage-only` runs a focused
coverage smoke on the config/domain unit-test slice with the current coverage
budget.

Plan evidence audit:

```bash
python3 scripts/verify_plan_evidence.py .omo/plans/2026-06-12-nfi-engine-dev-entry.md .omo/evidence/2026-06-12-dev-entry
```

## Milestone 1 Limits

- No real-money execution.
- No risky live-trading bypass.
- No profit promise or profitability claim.
- No public internet exposure for the operator console.
- No full upstream NFI parity claim.
- Exchange adapters are fixture/testnet oriented until later milestones.
- Current RC wording is paper/testnet only: live order execution remains behind
  a separate design and verification milestone.

## Further Reading

- [docs/release-wording.md](docs/release-wording.md)
- [docs/release-status.md](docs/release-status.md)
- [docs/docker.md](docs/docker.md)
- [docs/contributing.md](docs/contributing.md)
- [docs/freqtrade-feature-coverage.md](docs/freqtrade-feature-coverage.md)
- [docs/nfi-x7-compatibility.md](docs/nfi-x7-compatibility.md)
- [docs/exchange-support-matrix.md](docs/exchange-support-matrix.md)
- [docs/performance.md](docs/performance.md)
- [docs/plugins.md](docs/plugins.md)
- [docs/reproducibility.md](docs/reproducibility.md)
- [docs/circuit-breakers.md](docs/circuit-breakers.md)
- [docs/notifications.md](docs/notifications.md)
- [docs/sandbox.md](docs/sandbox.md)
- [docs/ui.md](docs/ui.md)
- [docs/operations.md](docs/operations.md)
- [docs/backup.md](docs/backup.md)
- [docs/reconciliation.md](docs/reconciliation.md)
- [docs/pairlist.md](docs/pairlist.md)
- [docs/simulator.md](docs/simulator.md)
