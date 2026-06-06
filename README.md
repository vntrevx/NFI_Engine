# NFI Engine

NFI Engine is an original, clean-room crypto trading engine for spot and futures
paper trading, deterministic simulation, and NFI-shaped strategy compatibility
research.

It is not Freqtrade, not an official NostalgiaForInfinity project, and not a
fork of either codebase. Freqtrade is used only as a feature benchmark for what a
serious operator engine should cover. Upstream NFI strategy code is not vendored
in this repository.

Milestone 1 is dry-run first. Real-money trading, unsafe live shortcuts, and
profit claims are out of scope.

## Quickstart

```bash
uv sync
uv run nfi-engine --help
uv run nfi-engine config validate --config examples/spot-paper.yaml
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml
uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/quickstart-backtest.json
```

Run the API and local operator console:

```bash
uv run nfi-engine serve --config examples/futures-paper.yaml --host 127.0.0.1 --port 18080
```

Open:

- `http://127.0.0.1:18080/settings`
- `http://127.0.0.1:18080/logs`

When `api.auth_token` is configured, create a browser session through the login
endpoint before using protected pages. Mutating API calls require the session
cookie and `x-nfi-csrf-token`.

## Docker Quickstart

```bash
docker build -t nfi-engine:local .
docker compose config
docker compose --profile paper up --build -d api
curl -i http://127.0.0.1:18080/api/v1/ping
docker compose run --rm cli nfi-engine config validate --config /app/examples/futures-paper.yaml
docker compose down -v
```

Compose binds the API to `127.0.0.1:18080` by default and uses named volumes for
data, logs, and config. Do not put exchange secrets in committed env files. See
[docs/docker.md](docs/docker.md).

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

## Evidence And Quality Gates

Use the smoke harness to refresh final evidence files:

```bash
bash scripts/final_smoke.sh
```

Core quality gate:

```bash
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest -q
```

Plan evidence audit:

```bash
python3 scripts/verify_plan_evidence.py .omo/plans/nfi-engine.md .omo/evidence
```

## Milestone 1 Limits

- No real-money execution.
- No unsafe live-trading bypass.
- No profit promise or profitability claim.
- No public internet exposure for the operator console.
- No full upstream NFI parity claim.
- Exchange adapters are fixture/testnet oriented until later milestones.

## Further Reading

- [docs/docker.md](docs/docker.md)
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
