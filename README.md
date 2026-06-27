# NFI Engine

[English](README.md) | [한국어](README.ko.md)

Local-first crypto trading engine for NFI-shaped X7 research, deterministic
paper runs, testnet operations, and safety-first exchange workflows.

NFI Engine is original clean-room software. It is not Freqtrade, not an official
NostalgiaForInfinity project, and not a fork. External projects are references
only; this repository does not vendor their strategy source, UI, docs, or
runtime code.

## Status

`v0.1.0-rc1` is a paper/testnet release candidate.

| Lane | Current state |
| --- | --- |
| Strategy | Native X7-shaped semantic runtime for inspect, dry-run, paper, and testnet-oriented paths. |
| Operator UI | Username/password login, Home cockpit, Settings setup, Logs, EN/KO/EL language switching. |
| Exchange setup | Capability registry, API permission audit, wallet balance fetch, leverage/allocation setup. |
| Safety | CSRF, read-only mode, live-intent blockers, wallet caps, reconciliation, circuit breakers, rollback gates. |
| Low-resource target | Raspberry Pi 4 stays an internal engineering budget, not a public speed claim. |
| Real-money live orders | Still locked behind a separate approved execution design and evidence set. |

Latest release notes: [docs/release-notes-v0.1.0-rc1.md](docs/release-notes-v0.1.0-rc1.md)
Current boundary: [docs/release-status.md](docs/release-status.md)

## Quickstart

Docker-first:

```bash
bash scripts/install.sh --yes --paper --testnet
```

npm or Bun wrappers:

```bash
npm run nfi:install
bun run nfi:install
```

Preview without starting anything:

```bash
bash scripts/install.sh --yes --paper --testnet --dry-run
npm run nfi:install:dry-run
bun run nfi:install:dry-run
```

First Run:

1. Open `http://127.0.0.1:18080/`.
2. Log in with username `admin` and the generated operator password from `.runtime/docker.env`.
3. Open Settings and walk the setup lane: exchange, API key/secret, permission audit, leverage, wallet balance, allocation, spot/futures, dry-run/live intent.
4. Keep dry-run selected unless you are testing the guarded live-intent path.
5. Use Logs when you need redacted support output.

API health:

```bash
curl -i http://127.0.0.1:18080/api/v1/ping
```

Uninstall:

```bash
bash scripts/uninstall.sh --yes
npm run nfi:uninstall
bun run nfi:uninstall
```

Safe uninstall keeps runtime files and volumes. Purge is explicit:

```bash
bash scripts/uninstall.sh --purge --yes
```

## What You Get

- Local operator console, no CDN dependency.
- Username/password session auth with CSRF protection.
- Exchange support promoted by capability evidence, not marketing lists.
- Wallet balance probe and permission audit before runtime decisions.
- Deterministic backtest, paper-run, simulator, and reconciliation surfaces.
- Native X7-shaped strategy inspection without vendoring upstream code.
- One-line install/uninstall for shell, npm, and Bun users.
- Release wording scan to block unsupported profit, parity, and live-money claims.

## X7 Runtime

Inspect the native X7-shaped runtime:

```bash
uv run nfi-engine strategy inspect \
  --config examples/x7-futures-paper.yaml \
  --strategy nfi_engine.strategy.nfi_x7:X7NativeStrategy \
  --json
```

This proves the engine-owned runtime boundary. It does not unlock real-money
orders.

## Developer Path

```bash
uv sync
uv run nfi-engine --help
uv run nfi-engine config validate --config examples/spot-paper.yaml
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml
uv run nfi-engine serve --config examples/futures-paper.yaml --host 127.0.0.1 --port 18080
```

Useful surfaces:

- `http://127.0.0.1:18080/`
- `http://127.0.0.1:18080/settings`
- `http://127.0.0.1:18080/logs`

Protected API calls require the session cookie and `x-nfi-csrf-token`. Exchange
credentials are write-only/redacted and must never be committed, pasted into
issues, or stored in shell history.

## Core Commands

```bash
uv run nfi-engine profile list
uv run nfi-engine config show --config examples/futures-paper.yaml
uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/pairlist.json
uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 25
uv run nfi-engine exchange capabilities --exchange bybit --trading-mode futures --format json
uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_match.json
uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/fill-sim.json
```

## Quality Gate

```bash
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest -q
uv run python scripts/release_wording_scan.py
bash scripts/final_smoke.sh
```

Docs-only pass:

```bash
bash scripts/quality_gate.sh --docs-only
bash scripts/quality_gate.sh --coverage-only  # coverage smoke
git diff --check
```

## Architecture

| Path | Job |
| --- | --- |
| `src/nfi_engine/config` | Typed runtime settings, migrations, redaction. |
| `src/nfi_engine/domain` | Market, pair, order, and trading-mode value objects. |
| `src/nfi_engine/strategy` | Clean strategy adapter and X7-shaped runtime boundary. |
| `src/nfi_engine/backtest` | Deterministic backtest and reproducibility metadata. |
| `src/nfi_engine/paper` | Paper runtime loop and state transitions. |
| `src/nfi_engine/exchange` | Capability registry, fixtures, reconciliation, fill simulation. |
| `src/nfi_engine/risk`, `safety`, `circuit_breakers` | Guardrails and hard stops. |
| `src/nfi_engine/api`, `src/nfi_engine/ui` | FastAPI API and local operator console. |
| `scripts` | Install, uninstall, smoke, release, and evidence helpers. |

## Docs

- [Docker](docs/docker.md)
- [UI](docs/ui.md)
- [Exchange Support Matrix](docs/exchange-support-matrix.md)
- [NFI X7 Compatibility](docs/nfi-x7-compatibility.md)
- [Release Wording Rules](docs/release-wording.md)
