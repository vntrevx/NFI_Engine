# NFI Engine

NFI Engine is an original, clean-room crypto trading engine for spot and futures
paper trading, deterministic simulation, and NFI-shaped strategy compatibility
research.

It is not Freqtrade, not an official NostalgiaForInfinity project, and not a
fork of either codebase. Freqtrade is used only as a feature benchmark for what a
serious operator engine should cover. Upstream NFI strategy code is not vendored
in this repository.

Milestone 1 is dry-run first. Real-money trading, risky live shortcuts, and
profit claims are out of scope.

Milestone 2 focuses on operator usability and product identity: simple setup,
home dashboard, local chart snapshots, English/Korean/Greek UI text,
one-command Docker install/uninstall, benchmark evidence, and a release gate
that proves the local operator flow before it is called shippable. See
[docs/freqtrade-feature-coverage.md](docs/freqtrade-feature-coverage.md) for the
clean-room feature map and NFI Engine differentiation rules.

## Quickstart

Docker is the primary first-run path. From a local checkout:

```bash
bash scripts/install.sh --yes --paper --testnet
```

First Run:

1. Open `http://127.0.0.1:18080/`.
2. Paste the local operator token from `.runtime/docker.env` into the login screen. The installer prints `login_token_file=.runtime/docker.env`, never the token value.
3. Use Home to check Setup Doctor, Safety Explainer, chart status, recent errors, and pairlist state.
4. Use Settings for the small Simple Mode form and setup preview. API key and API secret fields are write-only and redacted from output.
5. Use the language selector for English, Korean, and Greek UI text.
6. Use Logs to export a redacted support report when an error code appears.

Useful first checks:

```bash
curl -i http://127.0.0.1:18080/api/v1/ping
bash scripts/uninstall.sh --yes
```

Safe uninstall preserves generated runtime files and data volumes. Destructive
purge is explicit:

```bash
bash scripts/uninstall.sh --purge --yes
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
uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_match.json
uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/pairlist.json
uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/fill-sim.json
```

See [docs/operations.md](docs/operations.md), [docs/backup.md](docs/backup.md),
[docs/reconciliation.md](docs/reconciliation.md), [docs/pairlist.md](docs/pairlist.md),
and [docs/simulator.md](docs/simulator.md).

## Frontend Console

The console is a local operator surface, not a public dashboard.

- `/settings`: config metadata editor, validation, draft/apply, readiness, pairlist, safety locks.
- `/logs`: recent logs, severity filter, error-code lookup, correlation IDs, support report export.
- Read-only mode: settings/logs/pairlists are inspectable, while save/apply/restore/start/stop are disabled and server-blocked.
- Security: authenticated session cookie, CSRF token for mutations, logout, expiry, protected audit log, no browser token storage.

See [docs/ui.md](docs/ui.md).

## Feature Coverage

Freqtrade remains the functional benchmark, but NFI Engine must stay original in
design and implementation. Each broad feature category is tracked with an
explicit NFI Engine angle in
[docs/freqtrade-feature-coverage.md](docs/freqtrade-feature-coverage.md).

## Evidence And Quality Gates

Use the smoke harness to refresh final evidence files:

```bash
bash scripts/final_smoke.sh
```

The current M2 hardening evidence root is:

```text
.omo/evidence/2026-06-12-dev-entry/
```

The release gate includes Docker install/login/Home smoke, local benchmark JSON,
a supplied-baseline regression failure check, and desktop/mobile browser
evidence for Home, Settings, Logs, and the login path. Benchmark regression
blocking only applies when `--baseline` is supplied; first-run smoke validates
the generated local report without claiming public speed superiority.

Core quality gate:

```bash
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest -q
```

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

## Further Reading

- [docs/docker.md](docs/docker.md)
- [docs/contributing.md](docs/contributing.md)
- [docs/freqtrade-feature-coverage.md](docs/freqtrade-feature-coverage.md)
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
