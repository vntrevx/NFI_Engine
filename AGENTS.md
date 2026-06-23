# PROJECT KNOWLEDGE BASE

**Generated:** 2026-06-13T01:24:33+09:00
**Commit:** a0a0630
**Branch:** main

## OVERVIEW

NFI Engine is an original Python 3.12 crypto trading engine for paper/testnet
operation, deterministic simulation, backtesting, and NFI-shaped strategy
compatibility research. Freqtrade and NostalgiaForInfinity are behavior
references only; do not copy code, UI, wording, or distinctive design.

## STRUCTURE

```text
nfi_engine/
|-- src/nfi_engine/      # engine package: CLI, API, domain, trading services
|-- tests/               # unit, integration, e2e, and canonical fixtures
|-- docs/                # operator, safety, Docker, UI, compatibility rules
|-- examples/            # spot/futures paper configs
|-- scripts/             # install, uninstall, smoke, benchmark, evidence tools
|-- .omo/                # plans, evidence, workflow ledger; generated-heavy
|-- Dockerfile
|-- compose.yaml
`-- pyproject.toml
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| First run | `README.md`, `docs/docker.md`, `scripts/install.sh` | Docker-first local paper/testnet path. |
| CLI entry | `src/nfi_engine/cli.py`, `src/nfi_engine/cli_*.py` | Root Typer app fans out by command group. |
| Runtime config | `src/nfi_engine/config/` | Pydantic settings plus custom loader/env overrides. |
| API app | `src/nfi_engine/api/app.py`, `api/routes.py` | FastAPI factory and route wiring. |
| Operator UI | `src/nfi_engine/ui/`, `docs/ui.md` | Local HTML/CSS/JS console, no CDN. |
| Trading model | `src/nfi_engine/domain/`, `risk/`, `safety/` | Typed market/order/risk boundaries. |
| Backtests | `src/nfi_engine/backtest/`, `validation/` | Deterministic outputs and reproducibility metadata. |
| Paper runtime | `src/nfi_engine/paper/`, `exchange/` | Tick-driven loop, simulator/testnet boundary. |
| Storage | `src/nfi_engine/persistence/`, `maintenance/` | SQLite repositories, migrations, backups. |
| Tests | `tests/unit`, `tests/integration`, `tests/e2e` | Layered tests with strict pytest config. |
| Evidence | `.omo/evidence/` | Manual QA, smoke, benchmark, and plan evidence. |

## CODE MAP

| Symbol | Type | Location | Role |
| --- | --- | --- | --- |
| `main` | function | `src/nfi_engine/cli.py` | CLI console-script entry. |
| `create_app` | function | `src/nfi_engine/api/app.py` | Builds the FastAPI app and UI/API wiring. |
| `RuntimeSettings` | class | `src/nfi_engine/config/models.py` | Root Pydantic runtime model. |
| `create_order_intent` | function | `src/nfi_engine/domain/orders.py` | Typed order-intent construction. |
| `run_backtest` | function | `src/nfi_engine/backtest/runner.py` | Deterministic backtest loop. |
| `run_paper` | function | `src/nfi_engine/paper/runner.py` | Paper-run event loop. |
| `render_home_page` | function | `src/nfi_engine/ui/pages.py` | First operator surface renderer. |
| `PersistenceDatabase` | class | `src/nfi_engine/persistence/session.py` | Async SQLAlchemy database wrapper. |

## CONVENTIONS

- Use `uv`; the quality gate is `uv run ruff format --check .`,
  `uv run ruff check .`, `uv run basedpyright`, `uv run pytest -q`.
- Python is 3.12, `basedpyright` is strict, `ruff` selects `ALL`, and warnings are pytest errors.
- Keep config parsing at the edge. Pass typed Pydantic/domain values into services, not raw YAML dictionaries.
- Use Polars or local typed structures for new engine data. Do not introduce pandas outside compatibility adapters.
- User-visible, safety, runtime, UI, Docker, or performance work needs manual evidence under `.omo/evidence/`.
- Keep public wording precise: feature benchmark/inspiration is acceptable; clone, parity, and profit claims are not.
- When the user writes Korean, answer concisely in Korean unless code or repo text needs English.

## ANTI-PATTERNS

- Do not copy Freqtrade, FreqUI, NostalgiaForInfinity source, docs prose, layout, colors, or strategy internals.
- Do not add real-money execution, live shortcuts, public-profit claims, or live-order bypasses in milestone work.
- Do not expose the operator API publicly by default. Preserve loopback binding
  unless a hardened deployment task exists.
- Do not commit secrets, runtime `.env`, API tokens, exchange keys, SQLite
  runtime data, logs, caches, or `.omo/evidence` artifacts.
- Do not let UI code reach directly into storage rows, raw config dictionaries, or safety internals.
- Do not bypass auth, CSRF, read-only mode, sandbox checks, plugin allowlists,
  circuit breakers, reconciliation, or dry-run previews.
- Do not create large files casually; the project plan treats 250 pure LOC as a split pressure point.

## COMMANDS

```bash
uv sync
uv run nfi-engine --help
uv run nfi-engine config validate --config examples/futures-paper.yaml
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml
uv run nfi-engine serve --config examples/futures-paper.yaml --host 127.0.0.1 --port 18080
bash scripts/install.sh --yes --paper --testnet
bash scripts/uninstall.sh --yes
bash scripts/final_smoke.sh
python3 scripts/verify_plan_evidence.py .omo/plans/nfi-engine.md .omo/evidence
```

## NOTES

- No in-repo `AGENTS.md` existed before this init pass.
- The worktree often contains active `.omo` plans/evidence and user edits. Do
  not clean, revert, or normalize unrelated files.
- `compose.yaml` may contain `0.0.0.0` inside container allowlists; host
  publishing must remain loopback unless intentionally hardened.
- Treat `.omo/plans/nfi-engine.md` as the durable original plan; older drafts or
  generated evidence are not source-of-truth docs.
