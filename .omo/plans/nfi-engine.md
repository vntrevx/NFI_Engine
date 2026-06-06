# NFI Engine Modular Trading Bot Work Plan

## TL;DR
> **Summary**: Build an original Python crypto trading engine with Freqtrade-like capabilities as behavior references, not copied source or design. The first milestone delivers a strict Python scaffold, spot/futures domain model, plugin boundaries, strategy compatibility boundary, reproducible backtests, walk-forward validation, circuit breakers, notifications, strategy sandboxing, paper-run loop, REST API, CLI, simple frontend operator console, Docker runtime, simulator, Bybit testnet adapter hooks, operator profiles, preflight checks, migrations, backup/restore, exchange reconciliation, pairlist controls, realistic fill simulation, and frontend security hardening.
> **Deliverables**:
> - Greenfield Python package `nfi-engine` under `src/nfi_engine/`
> - Strict test/lint/type toolchain with `uv`, `pytest`, `ruff`, and `basedpyright`
> - Spot and futures domain model with leverage, margin, liquidation guardrails, and typed order/trade states
> - Plugin registry for strategies, exchanges, risk modules, notifiers, and data sources
> - Freqtrade-style strategy adapter boundary for NFI-shaped strategies
> - Historical backtest, reproducible result metadata, walk-forward validation, and deterministic paper-run surfaces
> - Circuit breaker and kill-switch services for drawdown, loss streak, stale data, API errors, slippage, and funding anomalies
> - Notification adapters for Discord, Telegram, webhook, and local JSONL sinks
> - Strategy sandbox controls that restrict direct filesystem, network, environment, and live-order access
> - REST API, CLI, and simple local frontend operator controls
> - Frontend settings/log console for safe config edits, recent logs, error-code lookup, and redacted support report bundles
> - Operator profiles, preflight readiness checks, settings/config version history, and rollback workflow
> - Database/config migrations, backup/restore, redacted diagnostic bundles, and exchange reconciliation
> - Pairlist management UI, market eligibility checks, realistic execution simulator, and frontend security controls
> - Dockerfile, Compose stack, container healthcheck, and container QA workflow
> - SQLite persistence via SQLAlchemy async repositories
> - Exchange simulator and Bybit testnet-ready CCXT adapter behind safety gates
> **Effort**: XL
> **Parallel**: YES - 6 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 4 -> Task 6 -> Task 10 -> Task 19 -> Task 21 -> Task 22 -> Task 23 -> Task 24 -> Task 25 -> Task 29 -> Task 30 -> Final Verification

## Context
### Original Request
- User wants to build a "crypto currency trading system NFI strategy engine".
- Use all Freqtrade capabilities as functional inspiration.
- Do not copy Freqtrade design; use it only as a motif/reference.
- Support both Spot and Future trading.
- Target strategy source: `https://github.com/iterativv/NostalgiaForInfinity`.
- Keep the engine modular and maintainable.
- Decide whether Python or another stack is best.

### Interview Summary
- No answer was received for product tradeoff questions, so defaults were applied.
- Stack decision: Python 3.12+ is the correct first stack because Freqtrade and NFI strategies are Python/Freqtrade-interface strategies, and starting with Rust/Go would shift milestone 1 into compatibility-layer work instead of engine proof.
- First exchange target: exchange simulator plus Bybit futures testnet adapter. Real-money order placement is explicitly out of milestone 1.
- First NFI target: Freqtrade-style adapter plus NFI-shaped fixtures and smoke compatibility. Full X7 parity/backtest is a later milestone after the adapter boundary is proven and an upstream SHA is pinned.
- First product surface: CLI + REST API + simple local frontend operator console + backtest + paper-run. The frontend is for settings, logs, error-code lookup, and report bundles; a full analytics/dashboard cockpit is out of milestone 1.
- First persistence target: SQLite through SQLAlchemy 2.x async repositories, with interfaces shaped so Postgres can be added later.
- Docker is first-class for milestone 1: build a non-root runtime image, local Compose stack, persistent volumes, healthcheck, and containerized CLI/REST/paper QA. Local Docker evidence on 2026-06-06 KST: `Docker version 29.4.0`, `Docker Compose version v5.1.2`.
- Additional architecture decisions accepted by the user: plugin-style extension boundaries, reproducible backtest metadata, walk-forward validation, circuit breakers/kill switches, notification adapters, strategy sandboxing, simple frontend settings/log/report controls, operator profiles, preflight checks, migrations, backup/restore, exchange reconciliation, pairlist management, realistic fill simulation, and frontend security controls are mandatory first-milestone features.

### Metis Review (gaps addressed)
- Metis worker was spawned but returned no substantive output after repeated waits; it was closed as inconclusive.
- Guardrails incorporated from direct evidence:
  - Avoid copying Freqtrade or NFI source, UI layout, docs prose, strategy internals, or naming wholesale because both upstream repos report GPL-3.0.
  - Do not claim full NFI X7 compatibility until the plan pins an exact upstream SHA and runs parity/smoke evidence against that target.
  - Keep real-money trading out of milestone 1. Futures and leverage logic must be modeled and tested, but exchange adapters must default to simulator/testnet/paper mode.
  - Prevent scope creep: no full analytics/dashboard cockpit beyond the simple settings/logs console, hyperopt, FreqAI clone, Telegram clone, producer/consumer clustering, or production deployment automation in this first plan.
  - Docker is required for repeatable operation, but containers must not become an excuse to expose the API publicly or bake secrets into images.
  - Extension points must be explicit plugin contracts, not import-time monkeypatching or global registries with arbitrary side effects.
  - Backtest results must be reproducible by config, strategy, data, engine version, and dependency lock digests.
  - Kill switches must be enforced by the engine before order placement, not only reported after a loss.
  - Notifications must be adapter-based and non-blocking; notifier failure cannot crash the bot loop.
  - Strategy sandboxing must protect engine state and secrets while preserving NFI-style strategy compatibility.
  - Backup/restore, migrations, exchange reconciliation, and pairlist changes must default to dry-run/preview before any mutating action.
  - Frontend controls must simplify operation without bypassing API auth, CSRF protections, safety gates, config validation, or redaction.
  - Every behavior must be verified through tests and a real surface: CLI, REST, browser, or tmux-driven command.

## Work Objectives
### Core Objective
Create a maintainable, modular, original crypto trading engine bot that provides Freqtrade-inspired trading capabilities, supports spot and futures, and can host NFI-style strategy logic through a compatibility boundary.

### Deliverables
- `pyproject.toml`, `uv.lock`, strict toolchain config, and project layout.
- `src/nfi_engine/domain/` typed primitives, enums, order/trade/position models, and market-mode rules.
- `src/nfi_engine/config/` Pydantic settings and YAML config parser.
- `src/nfi_engine/strategy/` native strategy protocol and Freqtrade-style adapter.
- `src/nfi_engine/plugins/` plugin contracts, registry, manifest parsing, and safe discovery.
- `src/nfi_engine/data/` candle, informative timeframe, and fixture data loading.
- `src/nfi_engine/backtest/` deterministic backtest runner.
- `src/nfi_engine/validation/` walk-forward and validation split runner.
- `src/nfi_engine/circuit_breakers/` kill-switch rules and enforcement service.
- `src/nfi_engine/notifications/` notifier protocol and adapters.
- `src/nfi_engine/sandbox/` strategy capability guard and restricted execution helpers.
- `src/nfi_engine/paper/` paper-run event loop.
- `src/nfi_engine/exchange/` simulator and CCXT/Bybit testnet adapter boundary.
- `src/nfi_engine/persistence/` SQLAlchemy async SQLite repositories.
- `src/nfi_engine/maintenance/` migration, backup/restore, diagnostic bundle, and config versioning workflows.
- `src/nfi_engine/profiles/` operator profile presets and preflight readiness checks.
- `src/nfi_engine/reconciliation/` exchange-vs-local state reconciliation and restart recovery checks.
- `src/nfi_engine/pairlist/` pairlist rules, market eligibility validation, and frontend/API services.
- `src/nfi_engine/api/` FastAPI control and status endpoints.
- `src/nfi_engine/ui/` simple FastAPI-served frontend for settings, logs, error-code lookup, and redacted support report bundles.
- `src/nfi_engine/cli.py` Typer CLI.
- `Dockerfile`, `.dockerignore`, `compose.yaml`, `examples/docker.env.example`, and `docs/docker.md`.
- `examples/` configs and fixtures for spot and futures.
- `tests/unit`, `tests/integration`, and `tests/e2e`.
- `.omo/evidence/` command transcripts for final QA.

### Definition of Done (verifiable conditions with commands)
- `command -v uv` returns an executable path after bootstrap.
- `uv run ruff format --check .` exits 0.
- `uv run ruff check .` exits 0.
- `uv run basedpyright` exits 0.
- `uv run pytest -q` exits 0.
- `uv run nfi-engine --help` exits 0 and lists `config`, `backtest`, `paper-run`, and `serve`.
- `uv run nfi-engine config validate --config examples/spot-paper.yaml` exits 0.
- `uv run nfi-engine config validate --config examples/futures-paper.yaml` exits 0.
- `uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/final-backtest.json` exits 0 and writes valid JSON with trades, equity, and summary fields.
- Backtest JSON includes `config_hash`, `strategy_hash`, `data_hash`, `engine_version`, `dependency_lock_hash`, and `created_at`.
- `uv run nfi-engine validate walk-forward --config examples/spot-paper.yaml --splits 3 --output .omo/evidence/final-walk-forward.json` exits 0.
- `uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 25` exits 0 and reports paper positions without live orders.
- `uv run nfi-engine plugins list --config examples/futures-paper.yaml` exits 0 and lists strategy, exchange, risk, notifier, and data plugin groups.
- `uv run nfi-engine circuit-breaker simulate --config tests/fixtures/config/daily-loss-limit.yaml` exits nonzero or reports `trading_halted=true`.
- `uv run nfi-engine notify test --config examples/futures-paper.yaml --channel jsonl --message smoke` exits 0 and writes a local notification event.
- `uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.unsafe:EnvReadingStrategy` exits nonzero with `SANDBOX_VIOLATION`.
- `uv run uvicorn nfi_engine.api.app:create_app --factory --host 127.0.0.1 --port 18080` starts the API.
- `curl -i http://127.0.0.1:18080/api/v1/ping` returns HTTP 200 and `{"status":"pong"}`.
- Authenticated REST calls can start, pause, stop, reload config, list strategies, return status, return profit, return health, read/validate/apply safe settings, read recent logs/events, look up error codes, and generate a redacted support report bundle for the paper engine.
- Browser QA against `http://127.0.0.1:18080/settings` can edit a safe setting, validate it, save a draft, apply/reload it when allowed, see the audit event, inspect recent logs, filter an error code, and export a redacted support report bundle.
- `uv run nfi-engine profile list` lists `local-paper`, `bybit-testnet`, `backtest-only`, and `readonly-debug`.
- `uv run nfi-engine preflight check --profile bybit-testnet --config examples/futures-paper.yaml` exits 0 or prints typed blocking readiness failures.
- `uv run nfi-engine db migrate --dry-run` and `uv run nfi-engine config migrate --dry-run --config examples/futures-paper.yaml` exit 0 with planned changes.
- `uv run nfi-engine backup create --config examples/futures-paper.yaml --output .omo/evidence/final-backup.zip` writes a redacted backup archive; `uv run nfi-engine backup verify .omo/evidence/final-backup.zip` exits 0.
- `uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_mismatch.json` reports mismatches without mutating exchange or local state.
- `uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/final-pairlist.json` exits 0 and reports whitelist, blacklist, market eligibility, and rejected pairs.
- `uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/final-fill-sim.json` exits 0 and writes partial-fill, latency, funding, and slippage fields.
- `docker build -t nfi-engine:local .` exits 0.
- `docker compose --profile paper up --build -d api` starts the API bound to `127.0.0.1`.
- `curl -i http://127.0.0.1:18080/api/v1/ping` against the Compose service returns HTTP 200 and `{"status":"pong"}`.
- `docker compose run --rm cli nfi-engine config validate --config /app/examples/futures-paper.yaml` exits 0.

### Must Have
- Python 3.12+.
- `uv` project management.
- `src/` layout.
- Strict type checking with `basedpyright` `typeCheckingMode = "all"`.
- Strict `ruff` with project-specific documented exceptions only.
- Pydantic v2 at config/API boundaries.
- Frozen dataclasses/NewTypes in the domain.
- `anyio` for async orchestration.
- FastAPI REST API.
- Typer CLI.
- Simple local frontend operator console served by the API, with settings forms, log viewer, error-code lookup, and redacted support-report export.
- Frontend settings must use simple grouped controls: selects for modes/strategies, toggles for booleans, numeric inputs/sliders for risk values, inline validation messages, and clear save/apply/reload states.
- Frontend copy and layout must stay operational and compact: no marketing hero, no dashboard-card mosaic, no decorative UI, and no hidden advanced YAML editor as the primary workflow.
- Frontend security must include authenticated sessions, CSRF protection for mutating actions, session expiry, read-only mode, and explicit locked controls for dangerous/live-trading fields.
- Operator profiles for `local-paper`, `bybit-testnet`, `backtest-only`, and `readonly-debug`.
- Preflight readiness checks for config validity, profile compatibility, API auth strength, exchange/testnet mode, pair validity, leverage/margin guardrails, DB accessibility, log paths, Docker volumes, and notifier dry-run status.
- DB migration and config migration framework with dry-run, version history, rollback preview, and explicit backup-before-mutate guard.
- Backup/restore workflow for SQLite DB, config, logs, profile metadata, strategy metadata, and redacted diagnostic bundles.
- Exchange reconciliation service that detects local DB vs exchange/testnet order/position/balance drift without mutating state by default.
- Pairlist management with whitelist, blacklist, liquidity/volatility filters, futures eligibility checks, and simple frontend controls.
- Realistic simulator scenarios for partial fills, latency, funding fees, liquidation near-misses, abnormal slippage, and exchange rejects.
- Docker runtime image, Compose stack, `.dockerignore`, non-root container user, healthcheck, local-only API port binding, and named/bind volumes for data/logs/config.
- SQLAlchemy 2.x async SQLite repositories.
- Exchange adapter protocol with simulator and Bybit testnet implementation seam.
- Plugin registry with typed plugin manifests, deterministic discovery, and allowlisted plugin groups.
- Strategy adapter protocol with Freqtrade-style method/callback support.
- Reproducible backtest metadata and walk-forward validation split support.
- Circuit breaker service enforcing daily loss, max drawdown, loss streak, stale candle stream, exchange API error burst, slippage, funding-rate anomaly, and manual kill-switch rules.
- Notification protocol with Discord, Telegram, generic webhook, and local JSONL adapters.
- Strategy sandbox guard for filesystem, network, environment-variable, subprocess, and direct live-order access.
- Spot and futures market modes, including long/short rules, leverage, margin mode, liquidation buffer, and CCXT-style futures pair parsing.
- Deterministic paper/backtest modes before live trading.
- Tests written before production changes in each task.
- Manual QA artifacts under `.omo/evidence/`.

### Must NOT Have
- Do not copy Freqtrade source, NFI source, FreqUI, UI layout, docs prose, strategy internals, comments, or distinctive design.
- Do not vendor GPL-3.0 source unless the user explicitly approves adopting GPL obligations.
- Do not place real exchange keys in repo.
- Do not send live real-money orders in milestone 1.
- Do not expose the API on `0.0.0.0` by default.
- Do not run the application container as root.
- Do not bake `.env`, exchange keys, SQLite runtime DBs, logs, `.omo/evidence`, `.git`, caches, or secrets into Docker images.
- Do not publish container ports on `0.0.0.0`; Compose must bind host ports to `127.0.0.1`.
- Do not load plugins from arbitrary paths by default; plugin roots must be configured and checked.
- Do not let plugin import side effects mutate engine state before manifest validation.
- Do not accept non-reproducible backtest reports without config/data/strategy/engine/dependency hashes.
- Do not let circuit breakers be notification-only; halted trading must block new order intents.
- Do not let notifier failures block order/risk loops or leak secrets.
- Do not run untrusted strategy code with unrestricted filesystem, network, environment, subprocess, or live-order capabilities.
- Do not let frontend sessions bypass API auth, CSRF checks, read-only mode, or safety gates.
- Do not restore backups, run migrations, rollback config, or reconcile exchange state without a dry-run/preview path and explicit operator confirmation.
- Do not include secrets, exchange keys, webhook tokens, session tokens, or unredacted config/logs in backup or diagnostic archives.
- Do not mutate real exchange state during reconciliation in milestone 1.
- Do not claim the realistic simulator exactly matches a live exchange; it is a risk-modeling approximation.
- Do not build a broad analytics dashboard/cockpit in milestone 1; only the simple settings/logs operator console is in scope.
- Do not implement hyperopt/FreqAI equivalent in milestone 1.
- Do not create files above 250 pure LOC; split modules by responsibility.
- Do not use pandas internally for new engine data. Use Polars/DuckDB for new data code, and isolate pandas only inside the compatibility adapter if required for NFI/Freqtrade-shaped strategies.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: TDD with `pytest`, `pytest-randomly`, `pytest-cov`, `ruff`, and `basedpyright`.
- QA policy: Every task has agent-executed scenarios through CLI, REST `curl`, browser/Playwright, or tmux.
- Evidence: `.omo/evidence/task-{N}-{slug}.{ext}`.
- First write a failing test for each task and capture RED output in `.omo/evidence/task-{N}-red.txt`.
- Implement the minimum code.
- Capture GREEN focused output in `.omo/evidence/task-{N}-green.txt`.
- Capture manual QA command/API transcript in the task evidence file.

## Execution Strategy
### Parallel Execution Waves
> Target: 5-8 tasks per wave. Dependencies are explicit; do not edit dependent code before its blocked-by tasks are green.

Wave 1: Task 1, Task 2, Task 3, Task 5

Wave 2: Task 4, Task 6, Task 7, Task 8

Wave 3: Task 9, Task 10, Task 11, Task 12

Wave 4: Task 13, Task 14, Task 15, Task 16, Task 17, Task 18, Task 19, Task 21

Wave 5: Task 20, Task 22, Task 23, Task 24, Task 28

Wave 6: Task 25, Task 26, Task 27, Task 29, Task 30

### Dependency Matrix (full, all tasks)
- Task 1 blocks all implementation tasks.
- Task 2 blocks Tasks 4, 6, 7, 8, 9, 10, 11, 12.
- Task 3 blocks Tasks 4, 6, 10, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 27.
- Task 4 blocks Tasks 6, 10, 11, 12, 14, 17, 18, 21.
- Task 5 blocks Tasks 9, 10, 13, 18, 27, 28.
- Task 6 blocks Tasks 10, 12, 14, 18, 28.
- Task 7 blocks Tasks 9, 10, 11, 12, 13, 24, 25, 26.
- Task 8 blocks Tasks 10, 11, 12, 13, 17, 19, 28.
- Task 9 blocks Tasks 10, 17, 23, 26, 27, 28.
- Task 10 blocks Tasks 11, 12, 14, 19, 26.
- Task 11 blocks Tasks 13, 15, 20, 22, 23, 24, 25, 26, 27, 29.
- Task 12 blocks Tasks 15, 16, 23, 24, 25, 26, 27, 28, 30.
- Task 13 blocks Tasks 15, 19, 20, 22, 23, 24, 25, 26, 27, 29.
- Task 14 blocks Tasks 15, 18, 21.
- Task 15 blocks Tasks 16, 17, 19, 21, 22, 23, 24, 25, 26, 27, 29, 30.
- Task 16 blocks Tasks 22, 23, 25, 29, 30, and Final Verification.
- Task 17 blocks Tasks 20, 21, 22, 23, 27, 30.
- Task 18 blocks Tasks 28, 30.
- Task 19 blocks Tasks 20, 22, 23, 26, 28, 30.
- Task 20 blocks Tasks 23, 25, 30.
- Task 21 blocks Tasks 22, 29, 30.
- Task 22 blocks Tasks 23, 24, 25, 27, 29, 30.
- Task 23 blocks Tasks 25, 26, 27, 29, 30.
- Task 24 blocks Tasks 25, 29, 30.
- Task 25 blocks Tasks 29, 30.
- Task 26 blocks Task 30.
- Task 27 blocks Tasks 29, 30.
- Task 28 blocks Task 30.
- Task 29 blocks Task 30 and Final Verification.
- Task 30 blocks Final Verification.

## TODOs
> Implementation + Test = ONE task. Never separate.
> EVERY task MUST have: References + Acceptance Criteria + QA Scenarios.

- [x] 1. Bootstrap Strict Python Project

  **What to do**: Initialize git if absent, install `uv` if absent, create `pyproject.toml`, `uv.lock`, `src/nfi_engine/`, `tests/unit`, `tests/integration`, `tests/e2e`, `.gitignore`, `.env.example`, and initial package metadata. Configure `ruff`, `basedpyright`, pytest, and console script `nfi-engine`.
  **Must NOT do**: Do not add trading logic in this task. Do not use Poetry, pipenv, or raw requirements files as the primary project manager.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: all tasks | Blocked By: none

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - stack and greenfield decision.
  - External: `https://docs.astral.sh/uv/` - `uv` install and project usage.
  - External: `https://docs.pytest.org/` - pytest test runner behavior.

  **Acceptance Criteria**:
  - [ ] `command -v uv` exits 0.
  - [ ] `uv run nfi-engine --help` exits 0.
  - [ ] `uv run ruff format --check .` exits 0.
  - [ ] `uv run ruff check .` exits 0.
  - [ ] `uv run basedpyright` exits 0.
  - [ ] `uv run pytest -q` exits 0.

  **QA Scenarios**:
  ```
  Scenario: CLI package boots
    Tool: tmux
    Steps: tmux new-session -d -s ulw-qa-task1 'cd /home/user/nfi_engine && uv run nfi-engine --help'; sleep 2; tmux capture-pane -pt ulw-qa-task1 -S -200 > .omo/evidence/task-1-bootstrap-cli.txt; tmux kill-session -t ulw-qa-task1
    Expected: transcript contains "Usage:" and "nfi-engine"
    Evidence: .omo/evidence/task-1-bootstrap-cli.txt

  Scenario: Quality gate starts clean
    Tool: bash
    Steps: uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest -q | tee .omo/evidence/task-1-bootstrap-quality.txt
    Expected: all commands exit 0
    Evidence: .omo/evidence/task-1-bootstrap-quality.txt
  ```

  **Commit**: YES | Message: `build(project): scaffold strict python engine package` | Files: `pyproject.toml`, `uv.lock`, `.gitignore`, `.env.example`, `src/nfi_engine/**`, `tests/**`

- [x] 2. Implement Typed Domain Model For Spot And Futures

  **What to do**: Add branded primitives, value objects, enums, and typed errors for pairs, trading mode, margin mode, side, order type, time in force, order state, trade state, leverage, liquidation buffer, stake, price, quantity, candle, signal, order intent, execution report, position, and account snapshot. Use exhaustive `match` for variants.
  **Must NOT do**: Do not call exchange APIs. Do not store raw dicts in public signatures. Do not model futures as a boolean flag.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: Tasks 4, 6, 7, 8, 9, 10, 11, 12 | Blocked By: Task 1

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Must Have - frozen dataclasses/NewTypes and strict typing.
  - External: `https://www.freqtrade.io/en/stable/leverage/` - spot/futures, leverage, margin, liquidation behavior references.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/domain -q` includes RED->GREEN tests for spot long-only rules, futures short support, leverage limits, liquidation buffer bounds, and futures pair parsing.
  - [ ] `uv run basedpyright src/nfi_engine/domain tests/unit/domain` exits 0.
  - [ ] Invalid states such as spot short, leverage below 1, and malformed futures pair fail at parse boundaries with typed errors.

  **QA Scenarios**:
  ```
  Scenario: Futures pair parses and normalizes
    Tool: bash
    Steps: uv run nfi-engine domain inspect-pair 'ETH/USDT:USDT' --mode futures | tee .omo/evidence/task-2-domain-futures.txt
    Expected: output includes base ETH, quote USDT, settle USDT, trading_mode futures
    Evidence: .omo/evidence/task-2-domain-futures.txt

  Scenario: Spot short is rejected
    Tool: bash
    Steps: uv run nfi-engine domain validate-order --pair BTC/USDT --mode spot --side short --type market 2>&1 | tee .omo/evidence/task-2-domain-spot-short.txt
    Expected: command exits nonzero and output includes typed error code SPOT_SHORT_NOT_ALLOWED
    Evidence: .omo/evidence/task-2-domain-spot-short.txt
  ```

  **Commit**: YES | Message: `feat(domain): model spot and futures trading states` | Files: `src/nfi_engine/domain/**`, `tests/unit/domain/**`

- [x] 3. Implement Config Parser And Safe Runtime Settings

  **What to do**: Add Pydantic v2 config models for engine, exchange, strategy, database, risk, backtest, paper-run, API, UI, and logging. Add YAML loader, env override support, frontend-editable field metadata, restart-required flags, sensitive/redacted field markers, and examples for `examples/spot-paper.yaml` and `examples/futures-paper.yaml`.
  **Must NOT do**: Do not allow live trading by default. Do not accept unknown config keys silently. Do not store secrets in example files.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: Tasks 4, 6, 10, 14, 16, 17, 18, 19, 20, 21, 22, 23, 24, 27 | Blocked By: Task 1

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - local bootstrap and strict dependencies.
  - External: `https://docs.pydantic.dev/latest/` - Pydantic v2 models and settings.
  - External: `https://www.freqtrade.io/en/stable/configuration/` - reference config categories, not copied schema.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/config -q` covers happy path, unknown key rejection, missing exchange key behavior, invalid futures margin mode, and disabled live trading default.
  - [ ] `uv run nfi-engine config validate --config examples/spot-paper.yaml` exits 0.
  - [ ] `uv run nfi-engine config validate --config examples/futures-paper.yaml` exits 0.
  - [ ] `uv run nfi-engine config validate --config tests/fixtures/config/live-without-confirmation.yaml` exits nonzero.
  - [ ] Config schema metadata marks which fields are frontend-editable, sensitive, restart-required, and safe to apply at runtime.

  **QA Scenarios**:
  ```
  Scenario: Spot paper config validates
    Tool: bash
    Steps: uv run nfi-engine config validate --config examples/spot-paper.yaml | tee .omo/evidence/task-3-config-spot.txt
    Expected: output includes "valid" and "trading_mode=spot"
    Evidence: .omo/evidence/task-3-config-spot.txt

  Scenario: Live config without explicit confirmation fails
    Tool: bash
    Steps: uv run nfi-engine config validate --config tests/fixtures/config/live-without-confirmation.yaml 2>&1 | tee .omo/evidence/task-3-config-live-denied.txt
    Expected: command exits nonzero and output includes LIVE_TRADING_REQUIRES_CONFIRMATION
    Evidence: .omo/evidence/task-3-config-live-denied.txt

  Scenario: Frontend config metadata is available
    Tool: bash
    Steps: uv run nfi-engine config schema --frontend --config examples/futures-paper.yaml | tee .omo/evidence/task-3-config-frontend-schema.txt
    Expected: output includes frontend_editable, sensitive, restart_required, and runtime_apply_safe markers
    Evidence: .omo/evidence/task-3-config-frontend-schema.txt
  ```

  **Commit**: YES | Message: `feat(config): add safe runtime configuration parser` | Files: `src/nfi_engine/config/**`, `examples/**`, `tests/unit/config/**`, `tests/fixtures/config/**`

- [x] 4. Add Strategy Protocol And Freqtrade-Style Adapter Boundary

  **What to do**: Define native strategy protocol and adapter protocol for Freqtrade-style methods: `populate_indicators`, `populate_entry_trend`, `populate_exit_trend`, `informative_pairs`, `custom_exit`, `custom_stake_amount`, `order_filled`, `adjust_trade_position`, `confirm_trade_entry`, `confirm_trade_exit`, `bot_loop_start`, and `leverage`. Add compatibility DTOs for metadata, runmode, trade, order, and DataProvider facades. Isolate pandas compatibility inside this module only when required.
  **Must NOT do**: Do not import Freqtrade as a runtime dependency in the engine core. Do not copy NFI strategy logic. Do not make DataProvider reach into persistence directly.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: Tasks 6, 10, 11, 12, 14, 17, 18, 21 | Blocked By: Tasks 1, 2, 3

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - X7 compatibility callback surface.
  - External: `https://www.freqtrade.io/en/stable/strategy-101/` - strategy method names and signal columns.
  - External: `https://www.freqtrade.io/en/stable/strategy-callbacks/` - callback behavior references.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/strategy -q` covers native strategy, Freqtrade-style adapter, missing optional callbacks, leverage callback, and DataProvider facade.
  - [ ] Adapter tests prove `enter_long`, `enter_short`, `exit_long`, `exit_short`, and `enter_tag` outputs become typed signals.
  - [ ] Adapter tests fail if lookahead-prone future rows are read in incremental mode.

  **QA Scenarios**:
  ```
  Scenario: Fixture strategy emits long and short signals
    Tool: bash
    Steps: uv run nfi-engine strategy inspect --strategy tests.fixtures.strategies.nfi_shape:NFISmokeStrategy --config examples/futures-paper.yaml | tee .omo/evidence/task-4-strategy-inspect.txt
    Expected: output includes strategy name, can_short=true, timeframe=5m, callbacks detected
    Evidence: .omo/evidence/task-4-strategy-inspect.txt

  Scenario: Missing required strategy method is rejected
    Tool: bash
    Steps: uv run nfi-engine strategy inspect --strategy tests.fixtures.strategies.invalid:MissingEntryStrategy --config examples/spot-paper.yaml 2>&1 | tee .omo/evidence/task-4-strategy-invalid.txt
    Expected: command exits nonzero and output includes STRATEGY_CONTRACT_ERROR
    Evidence: .omo/evidence/task-4-strategy-invalid.txt
  ```

  **Commit**: YES | Message: `feat(strategy): add freqtrade style adapter boundary` | Files: `src/nfi_engine/strategy/**`, `tests/unit/strategy/**`, `tests/fixtures/strategies/**`

- [x] 5. Add Candle Data Fixtures And Data Access Layer

  **What to do**: Implement Polars-based candle loading, validation, timeframe alignment, informative timeframe joins, and fixture loaders. Add deterministic BTC/USDT spot and BTC/USDT:USDT futures fixtures for 5m and informative 15m/1h windows.
  **Must NOT do**: Do not download live market data in unit tests. Do not use pandas outside strategy compatibility code.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: Tasks 9, 10, 13, 18, 27, 28 | Blocked By: Task 1

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - DataProvider compatibility needs.
  - External: `https://docs.pola.rs/` - Polars dataframe API.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/data -q` covers candle schema parsing, duplicate timestamp rejection, missing column rejection, timeframe alignment, and informative join behavior.
  - [ ] `uv run nfi-engine data inspect --candles tests/fixtures/candles/btc_usdt_5m.jsonl` exits 0.
  - [ ] Data access returns immutable typed candle batches to engine layers.

  **QA Scenarios**:
  ```
  Scenario: Valid 5m candle fixture inspects
    Tool: bash
    Steps: uv run nfi-engine data inspect --candles tests/fixtures/candles/btc_usdt_5m.jsonl | tee .omo/evidence/task-5-data-valid.txt
    Expected: output includes rows count, timeframe 5m, pair BTC/USDT
    Evidence: .omo/evidence/task-5-data-valid.txt

  Scenario: Duplicate timestamps are rejected
    Tool: bash
    Steps: uv run nfi-engine data inspect --candles tests/fixtures/candles/duplicate_timestamp.jsonl 2>&1 | tee .omo/evidence/task-5-data-duplicate.txt
    Expected: command exits nonzero and output includes CANDLE_DUPLICATE_TIMESTAMP
    Evidence: .omo/evidence/task-5-data-duplicate.txt
  ```

  **Commit**: YES | Message: `feat(data): add typed candle fixture loader` | Files: `src/nfi_engine/data/**`, `tests/unit/data/**`, `tests/fixtures/candles/**`

- [x] 6. Implement Deterministic Backtest Engine

  **What to do**: Build a backtest runner that loads config, candles, and strategy adapter; generates signals; simulates entries/exits; applies fees/slippage; enforces max open trades; tracks equity, drawdown, trade history, and profit. Support spot long-only and futures long/short simulations with leverage and liquidation buffer checks.
  **Must NOT do**: Do not claim parity with Freqtrade. Do not include hyperopt. Do not use live exchange data.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: Tasks 10, 12, 14, 18, 28 | Blocked By: Tasks 2, 3, 4, 5

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - lookahead safety must be first-class.
  - External: `https://github.com/freqtrade/freqtrade` - backtesting exists as feature reference only.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/backtest -q` covers no-signal, single long, single short futures, stoploss, fee, slippage, max-open-trades, and liquidation guard.
  - [ ] `uv run pytest tests/e2e/test_backtest_cli.py -q` covers CLI surface.
  - [ ] Backtest JSON schema includes `trades`, `equity_curve`, `summary`, `config_digest`, and `strategy`.

  **QA Scenarios**:
  ```
  Scenario: Spot backtest produces deterministic summary
    Tool: bash
    Steps: uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/task-6-backtest-spot.json | tee .omo/evidence/task-6-backtest-spot.txt
    Expected: command exits 0 and JSON contains summary.total_trades
    Evidence: .omo/evidence/task-6-backtest-spot.json

  Scenario: Futures liquidation guard blocks unsafe stoploss
    Tool: bash
    Steps: uv run nfi-engine backtest --config tests/fixtures/config/futures-liquidation-risk.yaml --timerange 2026-01-01:2026-01-07 2>&1 | tee .omo/evidence/task-6-backtest-liquidation.txt
    Expected: command exits nonzero and output includes LIQUIDATION_BUFFER_VIOLATION
    Evidence: .omo/evidence/task-6-backtest-liquidation.txt
  ```

  **Commit**: YES | Message: `feat(backtest): simulate spot and futures strategies` | Files: `src/nfi_engine/backtest/**`, `tests/unit/backtest/**`, `tests/e2e/test_backtest_cli.py`

- [x] 7. Implement Async SQLite Persistence Repositories

  **What to do**: Add SQLAlchemy async engine/session setup, migrations or metadata initialization, repositories for bot state, trades, orders, positions, locks, equity snapshots, and strategy custom data. Add repository protocols so Postgres can be added later without domain rewrites.
  **Must NOT do**: Do not leak ORM models into domain services. Do not require Postgres in milestone 1.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: Tasks 9, 10, 11, 12, 13, 24, 25, 26 | Blocked By: Tasks 1, 2, 3

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - X7 expects Trade/Order persistence semantics.
  - External: `https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html` - SQLAlchemy async usage.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/integration/persistence -q` covers create/read/update trades, orders, positions, locks, equity snapshots, transaction rollback, and custom data.
  - [ ] `uv run nfi-engine db init --config examples/spot-paper.yaml` creates a SQLite DB.
  - [ ] Domain code imports repository protocols, not SQLAlchemy ORM classes.

  **QA Scenarios**:
  ```
  Scenario: SQLite DB initializes
    Tool: bash
    Steps: rm -f .omo/evidence/task-7.sqlite; uv run nfi-engine db init --database-url sqlite+aiosqlite:///.omo/evidence/task-7.sqlite | tee .omo/evidence/task-7-db-init.txt
    Expected: output includes "initialized" and DB file exists
    Evidence: .omo/evidence/task-7-db-init.txt

  Scenario: Trade repository roundtrip
    Tool: bash
    Steps: uv run nfi-engine db smoke --database-url sqlite+aiosqlite:///.omo/evidence/task-7.sqlite | tee .omo/evidence/task-7-db-smoke.txt
    Expected: output includes created trade id and loaded trade id matching
    Evidence: .omo/evidence/task-7-db-smoke.txt
  ```

  **Commit**: YES | Message: `feat(persistence): add sqlite trading repositories` | Files: `src/nfi_engine/persistence/**`, `tests/integration/persistence/**`

- [x] 8. Implement Risk, Order, And Position Services

  **What to do**: Add services for stake sizing, wallet/account exposure, position opening/closing, order intent generation, order fill application, stoploss/ROI evaluation, pair locks, cooldowns, and futures leverage validation. Include spot long-only enforcement and futures long/short enforcement.
  **Must NOT do**: Do not combine risk service with exchange adapter. Do not permit live order intents unless runtime mode is explicitly `paper` or `testnet` in milestone 1.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: Tasks 10, 11, 12, 13, 17, 19, 28 | Blocked By: Tasks 2, 3, 7

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - V3 long/short terminology and leverage callback.
  - External: `https://www.freqtrade.io/en/stable/strategy-callbacks/` - stake, exit, adjustment, confirmation, leverage callback references.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/risk tests/unit/orders -q` covers stake limits, max open trades, pair locks, cooldown, stoploss, ROI, futures leverage, and live-order rejection.
  - [ ] Applying an execution report updates position and trade state deterministically.
  - [ ] Risk service has typed error outputs for rejected order intents.

  **QA Scenarios**:
  ```
  Scenario: Futures leverage is capped
    Tool: bash
    Steps: uv run nfi-engine risk quote --config examples/futures-paper.yaml --pair BTC/USDT:USDT --side short --stake 100 --leverage 999 | tee .omo/evidence/task-8-risk-leverage.txt
    Expected: output includes capped leverage and accepted=false or adjusted=true according to config max
    Evidence: .omo/evidence/task-8-risk-leverage.txt

  Scenario: Pair lock blocks entry
    Tool: bash
    Steps: uv run nfi-engine risk quote --config tests/fixtures/config/pair-locked.yaml --pair BTC/USDT --side long --stake 100 2>&1 | tee .omo/evidence/task-8-risk-lock.txt
    Expected: command exits nonzero or reports accepted=false with PAIR_LOCKED
    Evidence: .omo/evidence/task-8-risk-lock.txt
  ```

  **Commit**: YES | Message: `feat(risk): enforce trading safety rules` | Files: `src/nfi_engine/risk/**`, `src/nfi_engine/orders/**`, `tests/unit/risk/**`, `tests/unit/orders/**`

- [x] 9. Implement Exchange Simulator And Bybit Testnet Adapter Boundary

  **What to do**: Define exchange protocol for markets, balances, tickers, candles, order placement, cancellation, order status, funding rates, and leverage settings. Implement deterministic simulator. Add CCXT-backed Bybit testnet adapter behind config flag and dry-run guard. Add fake HTTP/wire tests for adapter mapping; do not require real credentials in CI.
  **Must NOT do**: Do not place real orders. Do not make CCXT objects visible outside adapter package. Do not make Bybit the only possible adapter shape.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: Tasks 10, 17, 23, 26, 27, 28 | Blocked By: Tasks 2, 3, 5, 7, 8

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - Bybit/Binance-style adapter in paper/testnet mode first.
  - External: `https://docs.ccxt.com/` - CCXT exchange API reference.
  - External: `https://www.freqtrade.io/en/stable/exchanges/` - exchange feature reference only.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/exchange tests/integration/exchange -q` covers simulator fills, rejected live mode, Bybit testnet config mapping, futures pair handling, and funding-rate unsupported fallback.
  - [ ] Simulator can replay tick fixtures and fill market/limit orders deterministically.
  - [ ] Bybit adapter refuses to initialize without `testnet=true` in milestone 1.

  **QA Scenarios**:
  ```
  Scenario: Simulator fills a market order
    Tool: bash
    Steps: uv run nfi-engine exchange simulate-order --config examples/spot-paper.yaml --pair BTC/USDT --side long --type market --stake 100 | tee .omo/evidence/task-9-exchange-sim-fill.txt
    Expected: output includes order_state=filled and no live_exchange=true
    Evidence: .omo/evidence/task-9-exchange-sim-fill.txt

  Scenario: Bybit live mode is blocked
    Tool: bash
    Steps: uv run nfi-engine exchange check --config tests/fixtures/config/bybit-live-denied.yaml 2>&1 | tee .omo/evidence/task-9-exchange-live-denied.txt
    Expected: command exits nonzero and output includes LIVE_EXCHANGE_DISABLED_FOR_MILESTONE
    Evidence: .omo/evidence/task-9-exchange-live-denied.txt
  ```

  **Commit**: YES | Message: `feat(exchange): add simulator and testnet adapter seam` | Files: `src/nfi_engine/exchange/**`, `tests/unit/exchange/**`, `tests/integration/exchange/**`

- [x] 10. Implement Paper-Run Bot Loop

  **What to do**: Add async bot loop that loads config, initializes repositories, exchange adapter, data provider, strategy adapter, risk/order services, then processes deterministic tick/candle events. Implement states `stopped`, `running`, `paused`, `stopping`. Persist trades/orders/positions and emit events.
  **Must NOT do**: Do not fire-and-forget tasks. Do not use `asyncio`; use `anyio`. Do not allow live exchange adapter unless explicitly testnet/paper.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: Tasks 11, 12, 14, 19, 26 | Blocked By: Tasks 2, 3, 4, 5, 6, 7, 8, 9

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - REST start/pause/stop/status benchmark.
  - External: `https://anyio.readthedocs.io/` - structured async task groups.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/paper tests/e2e/test_paper_run_cli.py -q` covers start, pause, resume, stop, max events, no signals, long signal, short signal, and persistence.
  - [ ] Bot loop shuts down cleanly without leaked tasks.
  - [ ] Paper-run command never initializes live order placement.

  **QA Scenarios**:
  ```
  Scenario: Futures paper run processes 25 events
    Tool: tmux
    Steps: tmux new-session -d -s ulw-qa-task10 'cd /home/user/nfi_engine && uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 25'; sleep 5; tmux capture-pane -pt ulw-qa-task10 -S -300 > .omo/evidence/task-10-paper-run.txt; tmux kill-session -t ulw-qa-task10
    Expected: transcript contains processed_events=25 and live_orders=false
    Evidence: .omo/evidence/task-10-paper-run.txt

  Scenario: Malformed tick stream fails gracefully
    Tool: bash
    Steps: uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/malformed.jsonl --max-events 25 2>&1 | tee .omo/evidence/task-10-paper-run-malformed.txt
    Expected: command exits nonzero and output includes TICK_PARSE_ERROR
    Evidence: .omo/evidence/task-10-paper-run-malformed.txt
  ```

  **Commit**: YES | Message: `feat(paper): run deterministic paper trading loop` | Files: `src/nfi_engine/paper/**`, `tests/unit/paper/**`, `tests/e2e/test_paper_run_cli.py`

- [x] 11. Implement REST API Control Surface

  **What to do**: Add FastAPI app factory and routes under `/api/v1`: `/ping`, `/health`, `/start`, `/pause`, `/stop`, `/reload_config`, `/status`, `/profit`, `/trades`, `/locks`, `/strategies`, `/strategy/{name}`, `/pair_history`, `/message/ws`, `/config/current`, `/config/schema`, `/config/draft`, `/config/validate`, `/config/apply`, `/logs/recent`, `/logs/search`, `/errors/{code}`, and `/reports/support-bundle`. Use auth for all endpoints except `/ping` and local development health if configured.
  **Must NOT do**: Do not expose API on `0.0.0.0` by default. Do not copy Freqtrade endpoint response schemas exactly; provide original typed schemas with familiar concepts.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: Tasks 13, 15, 20, 22, 23, 24, 25, 26, 27, 29 | Blocked By: Tasks 3, 4, 7, 8, 10

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - REST control benchmark.
  - External: `https://www.freqtrade.io/en/stable/rest-api/` - endpoint category reference only.
  - External: `https://fastapi.tiangolo.com/` - FastAPI app and testing.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/api tests/e2e/test_api_surface.py -q` covers ping, auth-required endpoints, start/pause/stop state transitions, status/profit/trades, strategy list, pair history, config read/validate/apply, logs search, error-code lookup, report bundle export, and websocket connection rejection without token.
  - [ ] API defaults to `127.0.0.1`.
  - [ ] Auth secret validation rejects weak defaults in non-dev mode.

  **QA Scenarios**:
  ```
  Scenario: Ping endpoint works
    Tool: HTTP call
    Steps: uv run uvicorn nfi_engine.api.app:create_app --factory --host 127.0.0.1 --port 18080 > .omo/evidence/task-11-api-server.log 2>&1 & echo $! > .omo/evidence/task-11-api.pid; sleep 3; curl -i http://127.0.0.1:18080/api/v1/ping | tee .omo/evidence/task-11-api-ping.txt; kill $(cat .omo/evidence/task-11-api.pid)
    Expected: response status is HTTP/1.1 200 OK or HTTP/1.1 200 and body contains {"status":"pong"}
    Evidence: .omo/evidence/task-11-api-ping.txt

  Scenario: Auth endpoint rejects missing token
    Tool: HTTP call
    Steps: uv run uvicorn nfi_engine.api.app:create_app --factory --host 127.0.0.1 --port 18081 > .omo/evidence/task-11-api-auth-server.log 2>&1 & echo $! > .omo/evidence/task-11-api-auth.pid; sleep 3; curl -i http://127.0.0.1:18081/api/v1/status | tee .omo/evidence/task-11-api-auth-missing.txt; kill $(cat .omo/evidence/task-11-api-auth.pid)
    Expected: response status is HTTP/1.1 401 or HTTP/1.1 403
    Evidence: .omo/evidence/task-11-api-auth-missing.txt

  Scenario: Config and log API endpoints serve frontend data
    Tool: HTTP call
    Steps: NFI_ENGINE_API_TOKEN=test-token uv run uvicorn nfi_engine.api.app:create_app --factory --host 127.0.0.1 --port 18082 > .omo/evidence/task-11-api-ui-server.log 2>&1 & echo $! > .omo/evidence/task-11-api-ui.pid; sleep 3; curl -i -H 'Authorization: Bearer test-token' http://127.0.0.1:18082/api/v1/config/schema | tee .omo/evidence/task-11-api-config-schema.txt; curl -i -H 'Authorization: Bearer test-token' 'http://127.0.0.1:18082/api/v1/logs/recent?limit=20' | tee .omo/evidence/task-11-api-logs-recent.txt; kill $(cat .omo/evidence/task-11-api-ui.pid)
    Expected: config response includes editable field metadata and logs response includes a typed list response
    Evidence: .omo/evidence/task-11-api-config-schema.txt, .omo/evidence/task-11-api-logs-recent.txt
  ```

  **Commit**: YES | Message: `feat(api): expose paper bot control endpoints` | Files: `src/nfi_engine/api/**`, `tests/unit/api/**`, `tests/e2e/test_api_surface.py`

- [x] 12. Implement CLI Operator Surface

  **What to do**: Add Typer commands: `config validate`, `config show`, `config schema`, `strategy inspect`, `data inspect`, `domain inspect-pair`, `domain validate-order`, `risk quote`, `exchange check`, `exchange simulate-order`, `db init`, `db smoke`, `backtest`, `paper-run`, and `serve`. Ensure each command has JSON and human output modes where useful.
  **Must NOT do**: Do not hide errors behind tracebacks for expected user errors. Do not create CLI-only behavior that bypasses service layer tests.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: Tasks 15, 16, 23, 24, 25, 26, 27, 28, 30 | Blocked By: Tasks 3, 4, 6, 7, 8, 10

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - CLI + REST first.
  - External: `https://typer.tiangolo.com/` - Typer CLI.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/e2e/test_cli_surface.py -q` covers help, config validation, backtest, paper-run, expected error exit code, and JSON output.
  - [ ] `uv run nfi-engine --help` lists all top-level command groups.
  - [ ] Expected user errors return nonzero with typed error code.

  **QA Scenarios**:
  ```
  Scenario: CLI help lists operator commands
    Tool: bash
    Steps: uv run nfi-engine --help | tee .omo/evidence/task-12-cli-help.txt
    Expected: output includes config, strategy, data, exchange, db, backtest, paper-run, serve
    Evidence: .omo/evidence/task-12-cli-help.txt

  Scenario: CLI JSON backtest output parses
    Tool: bash
    Steps: uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --json > .omo/evidence/task-12-cli-backtest.json; python3 -m json.tool .omo/evidence/task-12-cli-backtest.json > .omo/evidence/task-12-cli-backtest-pretty.txt
    Expected: json.tool exits 0 and pretty output includes summary
    Evidence: .omo/evidence/task-12-cli-backtest-pretty.txt
  ```

  **Commit**: YES | Message: `feat(cli): add operator command surface` | Files: `src/nfi_engine/cli.py`, `src/nfi_engine/commands/**`, `tests/e2e/test_cli_surface.py`

- [x] 13. Add Observability, Events, And Operator Logs

  **What to do**: Add structured event model and logging for bot state transitions, signals, order intents, fills, rejects, risk decisions, API actions, config changes, and paper/backtest summaries. Add JSONL event sink, typed error-code catalog, correlation IDs, recent-log query service, and in-memory event bus for websocket/API.
  **Must NOT do**: Do not log secrets, API keys, raw credentials, or private config values. Do not rely on print statements in production paths.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: Tasks 15, 19, 20, 22, 23, 24, 25, 26, 27, 29 | Blocked By: Tasks 7, 8, 10, 11

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - bot needs operator-visible dry-run/backtest behavior.
  - External: `https://www.structlog.org/` - structured logging reference.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/events tests/unit/observability -q` covers event serialization, secret redaction, JSONL sink, websocket fanout, logger context, correlation IDs, error-code catalog lookup, log filtering, and support-report redaction.
  - [ ] Paper-run writes JSONL events when configured.
  - [ ] Event schemas are typed Pydantic response models at API boundary.
  - [ ] Operator logs expose enough context for a user to report an error quickly: timestamp, severity, error code, correlation ID, command/API route, and redacted summary.

  **QA Scenarios**:
  ```
  Scenario: Paper run emits JSONL events
    Tool: bash
    Steps: rm -f .omo/evidence/task-13-events.jsonl; uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 5 --events .omo/evidence/task-13-events.jsonl | tee .omo/evidence/task-13-events-run.txt
    Expected: events file exists and contains bot_started plus bot_stopped
    Evidence: .omo/evidence/task-13-events.jsonl

  Scenario: Secret values are redacted
    Tool: bash
    Steps: uv run nfi-engine config show --config tests/fixtures/config/with-secret.yaml | tee .omo/evidence/task-13-redaction.txt
    Expected: output does not contain the fixture secret and includes REDACTED
    Evidence: .omo/evidence/task-13-redaction.txt

  Scenario: Error code can be explained from operator logs
    Tool: bash
    Steps: uv run nfi-engine logs explain CONFIG_VALIDATION_ERROR --events tests/fixtures/events/config_validation_error.jsonl | tee .omo/evidence/task-13-error-explain.txt
    Expected: output includes CONFIG_VALIDATION_ERROR, correlation_id, safe_summary, and report_hint
    Evidence: .omo/evidence/task-13-error-explain.txt
  ```

  **Commit**: YES | Message: `feat(observability): emit safe trading events` | Files: `src/nfi_engine/events/**`, `src/nfi_engine/observability/**`, `tests/unit/events/**`, `tests/unit/observability/**`

- [x] 14. Add NFI Compatibility Fixtures And SHA Pinning Workflow

  **What to do**: Add a clean-room NFI-shaped smoke strategy fixture that mimics interface shape but not NFI internals. Add metadata file recording checked upstream `iterativv/NostalgiaForInfinity` SHA/version and compatibility assumptions. Add optional command `compat nfi-check` that verifies local adapter support against the fixture and reports unsupported X7 surfaces. Do not import upstream X7 by default.
  **Must NOT do**: Do not copy `NostalgiaForInfinityX7.py`. Do not claim full X7 parity. Do not include referral/donation/comments from upstream strategy.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: Tasks 15, 18, 21 | Blocked By: Tasks 4, 6, 10

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context - local X7 version evidence.
  - Pattern: `.omo/plans/nfi-engine.md` Context - upstream X7 version drift and SHA pinning requirement.
  - External: `https://github.com/iterativv/NostalgiaForInfinity` - upstream strategy repository.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/compat tests/e2e/test_nfi_compat_cli.py -q` covers fixture adapter support, unsupported callback reporting, SHA metadata parsing, and no upstream source vendoring.
  - [ ] `uv run nfi-engine compat nfi-check --strategy tests.fixtures.strategies.nfi_shape:NFISmokeStrategy` exits 0.
  - [ ] A source scan verifies no copied `NostalgiaForInfinityX7.py` file exists in `src/`.

  **QA Scenarios**:
  ```
  Scenario: NFI-shaped fixture passes compatibility check
    Tool: bash
    Steps: uv run nfi-engine compat nfi-check --strategy tests.fixtures.strategies.nfi_shape:NFISmokeStrategy | tee .omo/evidence/task-14-nfi-check.txt
    Expected: output includes compatible=true and full_x7_parity=false
    Evidence: .omo/evidence/task-14-nfi-check.txt

  Scenario: Upstream source is not vendored
    Tool: bash
    Steps: rg -n 'NostalgiaForInfinityX7 by iterativ|long_normal_mode_tags|Referral Links' src tests || true | tee .omo/evidence/task-14-no-vendor-scan.txt
    Expected: output is empty or only points to explicit negative-test fixtures that do not copy upstream code
    Evidence: .omo/evidence/task-14-no-vendor-scan.txt
  ```

  **Commit**: YES | Message: `feat(compat): add nfi style strategy smoke checks` | Files: `src/nfi_engine/compat/**`, `tests/unit/compat/**`, `tests/e2e/test_nfi_compat_cli.py`, `docs/compatibility/nfi.md`

- [x] 15. Add Safety, Security, And Live-Trading Guardrails

  **What to do**: Add default local-only API binding, strong token requirement outside dev, CORS disabled by default, secrets redaction, dry-run/testnet-only enforcement, live trading confirmation gate, account-mode guard for futures, and explicit warnings for leverage. Add safety docs.
  **Must NOT do**: Do not enable live real-money trading. Do not expose API publicly by default. Do not log credentials.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: Tasks 16, 17, 19, 21, 22, 23, 24, 25, 26, 27, 29, 30 | Blocked By: Tasks 11, 12, 13, 14

  **References**:
  - External: `https://www.freqtrade.io/en/stable/rest-api/` - API exposure warning and auth concepts.
  - External: `https://www.freqtrade.io/en/stable/leverage/` - leverage risk warnings and one-bot-per-account assumption.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/safety tests/e2e/test_safety_gates.py -q` covers local bind default, weak token rejection, live trading denied, Bybit testnet allowed, CORS default deny, futures account exclusivity warning, and secret redaction.
  - [ ] API cannot start in production profile with default token.
  - [ ] Live mode command fails unless explicit confirmation config and separate later milestone flag are present.

  **QA Scenarios**:
  ```
  Scenario: API refuses weak production token
    Tool: bash
    Steps: uv run nfi-engine serve --config tests/fixtures/config/api-weak-token-prod.yaml 2>&1 | tee .omo/evidence/task-15-api-weak-token.txt
    Expected: command exits nonzero and output includes WEAK_API_TOKEN
    Evidence: .omo/evidence/task-15-api-weak-token.txt

  Scenario: Live trading is blocked
    Tool: bash
    Steps: uv run nfi-engine paper-run --config tests/fixtures/config/live-real-orders.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 1 2>&1 | tee .omo/evidence/task-15-live-blocked.txt
    Expected: command exits nonzero and output includes LIVE_TRADING_OUT_OF_SCOPE
    Evidence: .omo/evidence/task-15-live-blocked.txt
  ```

  **Commit**: YES | Message: `feat(safety): enforce local and paper trading defaults` | Files: `src/nfi_engine/safety/**`, `tests/unit/safety/**`, `tests/e2e/test_safety_gates.py`, `docs/safety.md`

- [x] 16. Add Docker Runtime, Compose Stack, And Container QA

  **What to do**: Add a production-shaped but local-safe container setup: multi-stage `Dockerfile`, `.dockerignore`, `compose.yaml`, `examples/docker.env.example`, named volumes for SQLite/data/logs, read-only config mount examples, non-root runtime user, image labels, healthcheck, and Compose services for `api`, `cli`, and optional `paper`. The API service must bind host port `127.0.0.1:18080:18080`, serve the local frontend console from the same local-only process, use simulator/testnet defaults, and run without real exchange secrets.
  **Must NOT do**: Do not run as root. Do not copy `.git`, `.env`, exchange credentials, runtime SQLite DB files, logs, `.omo/evidence`, caches, or local virtual environments into the image. Do not expose ports on `0.0.0.0`. Do not create production orchestration such as Kubernetes, Helm, Traefik, or cloud deployment in milestone 1.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: Tasks 22, 23, 25, 29, 30, and Final Verification | Blocked By: Tasks 11, 12, 15

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Context and Work Objectives - Docker is required for repeatable operation while retaining local-only API and no-secret guardrails.
  - External: `https://docs.docker.com/build/` - Docker image build reference.
  - External: `https://docs.docker.com/compose/` - Docker Compose reference.
  - External: `https://docs.astral.sh/uv/guides/integration/docker/` - `uv` container build patterns.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/e2e/test_docker_files.py -q` covers Dockerfile non-root runtime, `.dockerignore` secret/runtime exclusions, Compose local-only port binding, healthcheck presence, and named volume definitions.
  - [ ] `docker build -t nfi-engine:local .` exits 0.
  - [ ] `docker compose --profile paper up --build -d api` starts the API service.
  - [ ] `curl -i http://127.0.0.1:18080/api/v1/ping` against the Compose API returns HTTP 200 and `{"status":"pong"}`.
  - [ ] `curl -i http://127.0.0.1:18080/settings` against the Compose API returns local frontend HTML without requiring external CDN assets.
  - [ ] `docker compose run --rm cli nfi-engine config validate --config /app/examples/futures-paper.yaml` exits 0.
  - [ ] `docker compose down -v` removes the QA containers and volumes after the scenario.

  **QA Scenarios**:
  ```
  Scenario: Docker image builds
    Tool: bash
    Steps: docker build -t nfi-engine:local . 2>&1 | tee .omo/evidence/task-16-docker-build.txt
    Expected: command exits 0 and output includes "nfi-engine:local" or successful image export
    Evidence: .omo/evidence/task-16-docker-build.txt

	  Scenario: Compose API responds on local-only port
	    Tool: HTTP call
	    Steps: docker compose --profile paper up --build -d api; sleep 5; curl -i http://127.0.0.1:18080/api/v1/ping | tee .omo/evidence/task-16-compose-ping.txt; curl -i http://127.0.0.1:18080/settings | tee .omo/evidence/task-16-compose-settings.txt; docker compose down -v
	    Expected: ping response status is HTTP/1.1 200 OK or HTTP/1.1 200 and body contains {"status":"pong"}; settings response returns HTML from local assets
	    Evidence: .omo/evidence/task-16-compose-ping.txt, .omo/evidence/task-16-compose-settings.txt

  Scenario: Compose CLI validates futures config
    Tool: tmux
    Steps: tmux new-session -d -s ulw-qa-task16 'cd /home/user/nfi_engine && docker compose run --rm cli nfi-engine config validate --config /app/examples/futures-paper.yaml'; sleep 8; tmux capture-pane -pt ulw-qa-task16 -S -500 > .omo/evidence/task-16-compose-cli.txt; tmux kill-session -t ulw-qa-task16
    Expected: transcript contains "valid" and "trading_mode=futures"
    Evidence: .omo/evidence/task-16-compose-cli.txt
  ```

  **Commit**: YES | Message: `build(docker): add local paper trading container stack` | Files: `Dockerfile`, `.dockerignore`, `compose.yaml`, `examples/docker.env.example`, `docs/docker.md`, `tests/e2e/test_docker_files.py`

- [x] 17. Add Plugin Registry And Extension Contracts

  **What to do**: Add a typed plugin system for strategy, exchange, risk, notifier, and data providers. Implement plugin manifests, deterministic discovery from configured roots, allowlisted plugin groups, version compatibility checks, duplicate-name rejection, and registry inspection. Existing core adapters remain built-in plugins registered through the same interface.
  **Must NOT do**: Do not import arbitrary filesystem paths by default. Do not allow plugin import side effects before manifest validation. Do not use stringly typed plugin contracts.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: Tasks 20, 21, 22, 23, 27, 30 | Blocked By: Tasks 3, 4, 8, 9, 15

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Must Have - plugin registry with typed plugin manifests and allowlisted plugin groups.
  - Pattern: `src/nfi_engine/strategy/**` from Task 4 - strategy protocol to expose as plugin group.
  - Pattern: `src/nfi_engine/exchange/**` from Task 9 - exchange adapter protocol to expose as plugin group.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/plugins tests/e2e/test_plugins_cli.py -q` covers manifest parsing, deterministic ordering, duplicate rejection, incompatible version rejection, disabled plugin roots, and built-in plugin listing.
  - [ ] `uv run nfi-engine plugins list --config examples/futures-paper.yaml` exits 0 and lists `strategy`, `exchange`, `risk`, `notifier`, and `data` groups.
  - [ ] `uv run nfi-engine plugins inspect --name simulator-exchange --group exchange --json` exits 0 with manifest metadata.

  **QA Scenarios**:
  ```
  Scenario: Built-in plugin registry lists all groups
    Tool: bash
    Steps: uv run nfi-engine plugins list --config examples/futures-paper.yaml | tee .omo/evidence/task-17-plugins-list.txt
    Expected: output includes strategy, exchange, risk, notifier, and data
    Evidence: .omo/evidence/task-17-plugins-list.txt

  Scenario: Duplicate plugin names are rejected
    Tool: bash
    Steps: uv run nfi-engine plugins list --config tests/fixtures/config/duplicate-plugin-root.yaml 2>&1 | tee .omo/evidence/task-17-plugins-duplicate.txt
    Expected: command exits nonzero and output includes PLUGIN_DUPLICATE_NAME
    Evidence: .omo/evidence/task-17-plugins-duplicate.txt
  ```

  **Commit**: YES | Message: `feat(plugins): add typed extension registry` | Files: `src/nfi_engine/plugins/**`, `tests/unit/plugins/**`, `tests/e2e/test_plugins_cli.py`, `tests/fixtures/plugins/**`

- [x] 18. Add Reproducible Backtest Metadata And Walk-Forward Validation

  **What to do**: Extend backtest outputs with reproducibility metadata: config hash, strategy hash, data hash, engine version, git commit when available, dependency lock hash, Python version, created timestamp, and command arguments. Add walk-forward validation runner with explicit train/validation/test splits and aggregate metrics.
  **Must NOT do**: Do not claim profitability from walk-forward output. Do not silently reuse mutable local data without hashing it. Do not accept overlapping splits unless explicitly configured and tested.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: Tasks 28, 30 | Blocked By: Tasks 3, 4, 5, 6, 14

  **References**:
  - Pattern: `src/nfi_engine/backtest/**` from Task 6 - deterministic backtest output.
  - Pattern: `.omo/plans/nfi-engine.md` Definition of Done - required reproducibility metadata fields.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/backtest tests/unit/validation tests/e2e/test_walk_forward_cli.py -q` covers metadata hashing, changed config hash, changed data hash, strategy hash, dependency lock hash, non-overlapping split generation, malformed split rejection, and JSON output schema.
  - [ ] `uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/task-18-backtest.json` writes metadata fields.
  - [ ] `uv run nfi-engine validate walk-forward --config examples/spot-paper.yaml --splits 3 --output .omo/evidence/task-18-walk-forward.json` exits 0.

  **QA Scenarios**:
  ```
  Scenario: Backtest result includes reproducibility hashes
    Tool: bash
    Steps: uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/task-18-backtest.json && python3 -m json.tool .omo/evidence/task-18-backtest.json | tee .omo/evidence/task-18-backtest-metadata.txt
    Expected: output includes config_hash, strategy_hash, data_hash, engine_version, dependency_lock_hash
    Evidence: .omo/evidence/task-18-backtest-metadata.txt

  Scenario: Walk-forward validation emits split metrics
    Tool: bash
    Steps: uv run nfi-engine validate walk-forward --config examples/spot-paper.yaml --splits 3 --output .omo/evidence/task-18-walk-forward.json && python3 -m json.tool .omo/evidence/task-18-walk-forward.json | tee .omo/evidence/task-18-walk-forward.txt
    Expected: output includes splits and aggregate_metrics
    Evidence: .omo/evidence/task-18-walk-forward.txt
  ```

  **Commit**: YES | Message: `feat(backtest): record reproducible validation metadata` | Files: `src/nfi_engine/backtest/**`, `src/nfi_engine/validation/**`, `tests/unit/validation/**`, `tests/e2e/test_walk_forward_cli.py`

- [x] 19. Add Circuit Breakers And Kill-Switch Enforcement

  **What to do**: Implement circuit breakers for daily realized loss, equity drawdown, consecutive losses, stale candle stream, exchange/API error burst, abnormal slippage, funding-rate anomaly, manual halt file/flag, and max rejected-order burst. Circuit breakers must halt new order intents before exchange placement and emit typed events.
  **Must NOT do**: Do not make circuit breakers notification-only. Do not let a strategy bypass them. Do not close existing positions unless the specific breaker policy says emergency exit is enabled.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: Tasks 20, 22, 23, 26, 28, 30 | Blocked By: Tasks 3, 8, 10, 13, 15

  **References**:
  - Pattern: `src/nfi_engine/risk/**` from Task 8 - risk decision service.
  - Pattern: `src/nfi_engine/paper/**` from Task 10 - order intent flow.
  - Pattern: `src/nfi_engine/events/**` from Task 13 - typed event output.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/circuit_breakers tests/e2e/test_circuit_breakers_cli.py -q` covers every breaker type, reset policy, event emission, strategy bypass prevention, and halted order-intent rejection.
  - [ ] `uv run nfi-engine circuit-breaker simulate --config tests/fixtures/config/daily-loss-limit.yaml` reports `trading_halted=true`.
  - [ ] Paper-run stops opening new positions after breaker activation while preserving readable status.

  **QA Scenarios**:
  ```
  Scenario: Daily loss breaker halts trading
    Tool: bash
    Steps: uv run nfi-engine circuit-breaker simulate --config tests/fixtures/config/daily-loss-limit.yaml | tee .omo/evidence/task-19-daily-loss.txt
    Expected: output includes trading_halted=true and breaker=daily_loss
    Evidence: .omo/evidence/task-19-daily-loss.txt

  Scenario: Stale data breaker blocks new orders
    Tool: tmux
    Steps: tmux new-session -d -s ulw-qa-task19 'cd /home/user/nfi_engine && uv run nfi-engine paper-run --config tests/fixtures/config/stale-data-breaker.yaml --ticks tests/fixtures/ticks/stale_stream.jsonl --max-events 10'; sleep 8; tmux capture-pane -pt ulw-qa-task19 -S -500 > .omo/evidence/task-19-stale-data.txt; tmux kill-session -t ulw-qa-task19
    Expected: transcript includes STALE_DATA and new_orders_blocked=true
    Evidence: .omo/evidence/task-19-stale-data.txt
  ```

  **Commit**: YES | Message: `feat(safety): enforce circuit breakers before orders` | Files: `src/nfi_engine/circuit_breakers/**`, `tests/unit/circuit_breakers/**`, `tests/e2e/test_circuit_breakers_cli.py`

- [x] 20. Add Notification Adapter Layer

  **What to do**: Add notification protocol and adapters for local JSONL, generic webhook, Discord webhook, Telegram bot API, and no-op. Notifications must consume typed events from the event bus, redact secrets, retry with bounded backoff where safe, and never block the bot loop. Provide `notify test` CLI.
  **Must NOT do**: Do not send real external notifications in tests. Do not log tokens or chat IDs in cleartext. Do not crash trading loop on notifier failure.

  **Parallelization**: Can Parallel: YES | Wave 5 | Blocks: Tasks 23, 25, 30 | Blocked By: Tasks 11, 13, 17, 19

  **References**:
  - Pattern: `src/nfi_engine/events/**` from Task 13 - typed event stream.
  - Pattern: `src/nfi_engine/plugins/**` from Task 17 - notifier plugin group.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/notifications tests/integration/notifications tests/e2e/test_notify_cli.py -q` covers JSONL notification, webhook payload shape, Discord payload shape, Telegram payload shape, redaction, retry limit, timeout behavior, and bot-loop non-blocking behavior.
  - [ ] `uv run nfi-engine notify test --config examples/futures-paper.yaml --channel jsonl --message smoke` exits 0 and writes a local event.
  - [ ] HTTP notifier tests use local fake HTTP server only.

  **QA Scenarios**:
  ```
  Scenario: JSONL notifier writes smoke event
    Tool: bash
    Steps: rm -f .omo/evidence/task-20-notify.jsonl; uv run nfi-engine notify test --config examples/futures-paper.yaml --channel jsonl --message smoke --output .omo/evidence/task-20-notify.jsonl | tee .omo/evidence/task-20-notify-cli.txt
    Expected: command exits 0 and JSONL file contains message smoke
    Evidence: .omo/evidence/task-20-notify.jsonl

  Scenario: Webhook timeout is non-fatal
    Tool: bash
    Steps: uv run nfi-engine notify test --config tests/fixtures/config/webhook-timeout.yaml --channel webhook --message timeout-smoke 2>&1 | tee .omo/evidence/task-20-webhook-timeout.txt
    Expected: output includes notification_failed=true and process exits with documented non-fatal status
    Evidence: .omo/evidence/task-20-webhook-timeout.txt
  ```

  **Commit**: YES | Message: `feat(notifications): add event notifier adapters` | Files: `src/nfi_engine/notifications/**`, `tests/unit/notifications/**`, `tests/integration/notifications/**`, `tests/e2e/test_notify_cli.py`

- [x] 21. Add Strategy Sandbox And Capability Policy

  **What to do**: Add strategy sandbox policy around adapter execution. Strategies receive only approved capabilities: candle/data provider facade, typed config view, trade/order snapshots, and callback context. Detect and block direct environment reads, unauthorized filesystem writes, subprocess calls, direct network calls, and direct live-order access in compatibility fixture tests. Provide `sandbox check` CLI for strategy modules.
  **Must NOT do**: Do not promise OS-level hard sandboxing in Python. Do not break approved NFI-style callbacks. Do not expose raw secrets or exchange clients to strategies.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: Tasks 22, 29, 30 | Blocked By: Tasks 4, 14, 15, 17

  **References**:
  - Pattern: `src/nfi_engine/strategy/**` from Task 4 - adapter execution boundary.
  - Pattern: `src/nfi_engine/compat/**` from Task 14 - NFI-style fixture compatibility.
  - Pattern: `src/nfi_engine/plugins/**` from Task 17 - strategy plugin loading.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/sandbox tests/e2e/test_sandbox_cli.py -q` covers allowed DataProvider access, denied env read, denied filesystem write, denied subprocess, denied direct network, denied direct exchange client access, and NFI fixture compatibility.
  - [ ] `uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.nfi_shape:NFISmokeStrategy` exits 0.
  - [ ] `uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.unsafe:EnvReadingStrategy` exits nonzero with `SANDBOX_VIOLATION`.

  **QA Scenarios**:
  ```
  Scenario: NFI-shaped strategy passes sandbox policy
    Tool: bash
    Steps: uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.nfi_shape:NFISmokeStrategy | tee .omo/evidence/task-21-sandbox-safe.txt
    Expected: output includes sandbox_passed=true
    Evidence: .omo/evidence/task-21-sandbox-safe.txt

  Scenario: Environment-reading strategy is blocked
    Tool: bash
    Steps: uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.unsafe:EnvReadingStrategy 2>&1 | tee .omo/evidence/task-21-sandbox-env.txt
    Expected: command exits nonzero and output includes SANDBOX_VIOLATION
    Evidence: .omo/evidence/task-21-sandbox-env.txt
  ```

  **Commit**: YES | Message: `feat(strategy): enforce sandbox capability policy` | Files: `src/nfi_engine/sandbox/**`, `tests/unit/sandbox/**`, `tests/e2e/test_sandbox_cli.py`, `tests/fixtures/strategies/unsafe.py`

- [x] 22. Add Simple Frontend Operator Console For Settings And Logs

  **What to do**: Add a simple local frontend served by FastAPI for `/settings` and `/logs`. The settings view must be schema-driven from config metadata and support safe field editing, validation, draft save, apply/reload states, and audit feedback. The logs view must show recent operator logs/events, severity filter, error-code lookup, correlation ID, safe summary, and one-click redacted support report bundle export. Keep the UI operational and compact: tabs/sections, clear labels, selects/toggles/numeric inputs/sliders where appropriate, inline validation, and no decorative dashboard layout.
  **Must NOT do**: Do not build a broad analytics dashboard, performance cockpit, marketing landing page, hero, card mosaic, or trading-game UI. Do not expose secrets, raw config credentials, stack traces with sensitive values, or unredacted report bundles. Do not make raw YAML editing the primary settings workflow. Do not add live real-money controls.

  **Parallelization**: Can Parallel: YES | Wave 5 | Blocks: Tasks 23, 24, 25, 27, 29, 30 | Blocked By: Tasks 3, 11, 13, 15, 16, 17, 19, 21

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Must Have - simple local frontend operator console and no broad dashboard.
  - Pattern: `src/nfi_engine/config/**` from Task 3 - frontend-editable config metadata, sensitive flags, and restart-required flags.
  - Pattern: `src/nfi_engine/api/**` from Task 11 - config/log/error/report endpoints.
  - Pattern: `src/nfi_engine/events/**` from Task 13 - typed logs, error-code catalog, correlation IDs, and redacted support-report data.
  - Local skill guidance: `frontend-skill` app UI defaults - calm operational surface, dense but readable layout, utility copy, no dashboard-card mosaic.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/ui tests/e2e/test_settings_logs_ui.py -q` covers initial render, schema-driven controls, inline validation errors, draft save, safe apply/reload, unsafe live-setting block, audit event display, recent logs, severity filter, error-code lookup, correlation ID display, and redacted report bundle export.
  - [ ] `curl -i http://127.0.0.1:18080/settings` returns local HTML and does not reference external CDN assets.
  - [ ] Browser QA can edit a safe numeric risk/config field, validate it, save it as a draft, apply it when runtime-safe, and see a config audit event without touching raw YAML.
  - [ ] Browser QA can open recent logs, filter by error severity, inspect an error code, copy/report the correlation ID, and export a redacted support bundle.
  - [ ] Frontend does not render secrets, private config values, exchange keys, webhook tokens, raw stack traces with secrets, or any live real-money enable button.
  - [ ] UI stays intentionally simple: settings/logs tabs, compact grouped forms, clear states, no hero section, no card-heavy dashboard, no decorative charts.

  **QA Scenarios**:
  ```
  Scenario: Settings UI edits and validates a safe draft
    Tool: browser/Playwright
    Steps: start `uv run nfi-engine serve --config examples/futures-paper.yaml --host 127.0.0.1 --port 18080`; open http://127.0.0.1:18080/settings; change a safe field such as max_open_trades or stake amount; click Validate; click Save draft; click Apply when marked runtime-safe; capture screenshot to .omo/evidence/task-22-settings-ui.png and browser transcript to .omo/evidence/task-22-settings-ui.txt
    Expected: validation succeeds, draft saved state is visible, apply/reload state is explicit, and an audit event appears without exposing raw YAML or secrets
    Evidence: .omo/evidence/task-22-settings-ui.png, .omo/evidence/task-22-settings-ui.txt

  Scenario: Logs UI explains error code and exports support report
    Tool: browser/Playwright
    Steps: start API with seeded fixture logs including CONFIG_VALIDATION_ERROR; open http://127.0.0.1:18080/logs; filter severity=error; search CONFIG_VALIDATION_ERROR; open error details; click Export support report; save screenshot to .omo/evidence/task-22-logs-ui.png and exported bundle to .omo/evidence/task-22-support-report.zip
    Expected: page shows timestamp, severity, error code, correlation ID, redacted summary, and report hint; exported bundle contains redacted config/log context only
    Evidence: .omo/evidence/task-22-logs-ui.png, .omo/evidence/task-22-support-report.zip
  ```

  **Commit**: YES | Message: `feat(ui): add simple settings and logs console` | Files: `src/nfi_engine/ui/**`, `src/nfi_engine/api/**`, `src/nfi_engine/events/**`, `tests/unit/ui/**`, `tests/e2e/test_settings_logs_ui.py`, `docs/ui.md`

- [x] 23. Add Operator Profiles And Preflight Readiness Checks

  **What to do**: Add operator profiles `local-paper`, `bybit-testnet`, `backtest-only`, and `readonly-debug`. Add preflight readiness checks for config validity, selected profile compatibility, API token strength, local bind, Docker volume paths, SQLite access, log path writability, pair validity, market mode, leverage/margin guardrails, testnet/simulator exchange mode, notifier dry-run status, and live-order disabled state. Expose CLI, REST, and frontend readiness panel.
  **Must NOT do**: Do not start the bot from preflight. Do not call real exchange endpoints unless a testnet adapter is explicitly configured and testnet-safe. Do not downgrade blocking readiness failures to warnings.

  **Parallelization**: Can Parallel: YES | Wave 5 | Blocks: Tasks 25, 26, 27, 29, 30 | Blocked By: Tasks 3, 9, 11, 12, 13, 15, 16, 17, 19, 20, 22

  **References**:
  - Pattern: `src/nfi_engine/config/**` from Task 3 - typed config and frontend metadata.
  - Pattern: `src/nfi_engine/exchange/**` from Task 9 - simulator/testnet adapter boundary.
  - Pattern: `src/nfi_engine/api/**` and `src/nfi_engine/ui/**` from Tasks 11 and 22 - local operator surfaces.
  - Pattern: `src/nfi_engine/circuit_breakers/**` from Task 19 - readiness failures must block unsafe starts.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/profiles tests/unit/preflight tests/e2e/test_preflight_cli.py -q` covers profile loading, profile/config mismatch, missing DB path, unwritable log path, public API bind, weak token, live mode block, invalid futures leverage, disabled notifier warning, and Docker volume check.
  - [ ] `uv run nfi-engine profile list` lists `local-paper`, `bybit-testnet`, `backtest-only`, and `readonly-debug`.
  - [ ] `uv run nfi-engine preflight check --profile bybit-testnet --config examples/futures-paper.yaml` exits 0 for fixture-safe config or emits typed blocking failures.
  - [ ] Frontend readiness panel shows pass/warn/block groups and blocks start when any blocking check fails.

  **QA Scenarios**:
  ```
  Scenario: Operator profiles are listed
    Tool: bash
    Steps: uv run nfi-engine profile list | tee .omo/evidence/task-23-profile-list.txt
    Expected: output includes local-paper, bybit-testnet, backtest-only, and readonly-debug
    Evidence: .omo/evidence/task-23-profile-list.txt

  Scenario: Preflight blocks unsafe public API bind
    Tool: bash
    Steps: uv run nfi-engine preflight check --profile local-paper --config tests/fixtures/config/api-public-bind.yaml 2>&1 | tee .omo/evidence/task-23-preflight-public-bind.txt
    Expected: command exits nonzero and output includes PREFLIGHT_BLOCKED and PUBLIC_BIND_NOT_ALLOWED
    Evidence: .omo/evidence/task-23-preflight-public-bind.txt
  ```

  **Commit**: YES | Message: `feat(ops): add profiles and preflight checks` | Files: `src/nfi_engine/profiles/**`, `src/nfi_engine/preflight/**`, `src/nfi_engine/api/**`, `src/nfi_engine/ui/**`, `tests/unit/profiles/**`, `tests/unit/preflight/**`, `tests/e2e/test_preflight_cli.py`

- [x] 24. Add Migration, Version History, And Rollback Services

  **What to do**: Add Alembic-backed SQLite migration workflow, config schema-version migrator, immutable config/strategy version history records, rollback preview, and rollback apply guard. Every mutating migration or rollback must require a valid backup reference or an explicit `--allow-no-backup-for-dev` flag accepted only in dev fixtures.
  **Must NOT do**: Do not mutate DB/config by default. Do not run migrations at import time. Do not silently discard unknown config keys during migration. Do not rollback secrets into logs or frontend output.

  **Parallelization**: Can Parallel: YES | Wave 5 | Blocks: Tasks 25, 29, 30 | Blocked By: Tasks 3, 7, 11, 12, 13, 15, 22

  **References**:
  - Pattern: `src/nfi_engine/persistence/**` from Task 7 - SQLite repository boundaries.
  - Pattern: `src/nfi_engine/config/**` from Task 3 - strict Pydantic config parsing.
  - External: `https://alembic.sqlalchemy.org/` - SQLAlchemy migration workflow.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/maintenance tests/e2e/test_migrations_cli.py -q` covers DB dry-run, DB apply with backup, config dry-run, unknown key rejection, version history creation, rollback preview, rollback apply with backup, and secret redaction.
  - [ ] `uv run nfi-engine db migrate --dry-run --database tests/fixtures/db/v0.sqlite` exits 0 and prints migration plan.
  - [ ] `uv run nfi-engine config migrate --dry-run --config tests/fixtures/config/v0-config.yaml` exits 0 and prints schema-version changes.
  - [ ] `uv run nfi-engine config history --config examples/futures-paper.yaml` lists current config hash and version metadata.

  **QA Scenarios**:
  ```
  Scenario: DB migration dry-run previews changes
    Tool: bash
    Steps: uv run nfi-engine db migrate --dry-run --database tests/fixtures/db/v0.sqlite | tee .omo/evidence/task-24-db-migrate-dry-run.txt
    Expected: output includes migration_plan and apply=false
    Evidence: .omo/evidence/task-24-db-migrate-dry-run.txt

  Scenario: Config rollback requires backup
    Tool: bash
    Steps: uv run nfi-engine config rollback --to-version previous --config examples/futures-paper.yaml 2>&1 | tee .omo/evidence/task-24-rollback-no-backup.txt
    Expected: command exits nonzero and output includes BACKUP_REQUIRED
    Evidence: .omo/evidence/task-24-rollback-no-backup.txt
  ```

  **Commit**: YES | Message: `feat(maintenance): add migrations and config history` | Files: `src/nfi_engine/maintenance/**`, `src/nfi_engine/config/**`, `alembic.ini`, `migrations/**`, `tests/unit/maintenance/**`, `tests/e2e/test_migrations_cli.py`

- [x] 25. Add Backup, Restore, And Diagnostic Bundle Workflow

  **What to do**: Add backup creation, backup verification, restore dry-run, restore apply guard, and diagnostic support bundle generation. Backup archives include SQLite DB, sanitized config, selected logs, profile metadata, strategy metadata hash, engine version, dependency lock hash, Docker info when available, and manifest checksums. Diagnostic bundles must be redacted by default and usable from CLI, REST, and frontend.
  **Must NOT do**: Do not include raw secrets, exchange keys, webhook tokens, session tokens, unredacted stack traces, `.env`, `.git`, caches, or `.omo/evidence` in archives. Do not restore unless archive verification and dry-run pass.

  **Parallelization**: Can Parallel: YES | Wave 6 | Blocks: Tasks 29, 30 | Blocked By: Tasks 7, 11, 13, 15, 16, 20, 22, 23, 24

  **References**:
  - Pattern: `src/nfi_engine/events/**` from Task 13 - redaction and correlation IDs.
  - Pattern: `src/nfi_engine/ui/**` from Task 22 - frontend report export.
  - Pattern: `src/nfi_engine/maintenance/**` from Task 24 - backup-before-mutate guard.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/maintenance tests/e2e/test_backup_cli.py -q` covers backup create, manifest checksums, redaction, archive verification, restore dry-run, invalid archive rejection, backup-before-migration integration, and frontend/API diagnostic bundle export.
  - [ ] `uv run nfi-engine backup create --config examples/futures-paper.yaml --output .omo/evidence/task-25-backup.zip` exits 0.
  - [ ] `uv run nfi-engine backup verify .omo/evidence/task-25-backup.zip` exits 0.
  - [ ] `uv run nfi-engine backup restore --dry-run .omo/evidence/task-25-backup.zip` exits 0 and prints restore plan without mutating files.

  **QA Scenarios**:
  ```
  Scenario: Redacted backup archive verifies
    Tool: bash
    Steps: rm -f .omo/evidence/task-25-backup.zip; uv run nfi-engine backup create --config examples/futures-paper.yaml --output .omo/evidence/task-25-backup.zip && uv run nfi-engine backup verify .omo/evidence/task-25-backup.zip | tee .omo/evidence/task-25-backup-verify.txt
    Expected: verification exits 0 and output includes manifest_valid=true and redacted=true
    Evidence: .omo/evidence/task-25-backup.zip, .omo/evidence/task-25-backup-verify.txt

  Scenario: Restore dry-run does not mutate runtime files
    Tool: bash
    Steps: uv run nfi-engine backup restore --dry-run .omo/evidence/task-25-backup.zip | tee .omo/evidence/task-25-restore-dry-run.txt
    Expected: output includes restore_plan and apply=false
    Evidence: .omo/evidence/task-25-restore-dry-run.txt
  ```

  **Commit**: YES | Message: `feat(maintenance): add backup and diagnostic bundles` | Files: `src/nfi_engine/maintenance/**`, `src/nfi_engine/api/**`, `src/nfi_engine/ui/**`, `tests/unit/maintenance/**`, `tests/e2e/test_backup_cli.py`

- [x] 26. Add Exchange State Reconciliation And Startup Recovery

  **What to do**: Add reconciliation service comparing local DB state with simulator/testnet exchange snapshots for open orders, closed orders, positions, balances, leverage, margin mode, and pending cancels. Add startup recovery check that reports orphan orders, position mismatch, duplicate local trades, missing exchange fills, and stale local locks. Reconciliation defaults to dry-run and can only suggest actions in milestone 1.
  **Must NOT do**: Do not mutate real exchange state. Do not auto-close positions. Do not delete local records. Do not hide mismatches behind warnings when they affect trading safety.

  **Parallelization**: Can Parallel: YES | Wave 6 | Blocks: Task 30 | Blocked By: Tasks 7, 8, 9, 10, 11, 13, 15, 19, 23

  **References**:
  - Pattern: `src/nfi_engine/persistence/**` from Task 7 - order/trade/position repositories.
  - Pattern: `src/nfi_engine/exchange/**` from Task 9 - exchange adapter snapshots.
  - Pattern: `src/nfi_engine/circuit_breakers/**` from Task 19 - safety halt behavior when drift blocks trading.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/reconciliation tests/e2e/test_reconcile_cli.py -q` covers matching state, orphan local order, orphan exchange order, position size mismatch, balance mismatch, leverage mismatch, stale lock, startup recovery report, and dry-run action suggestions.
  - [ ] `uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_match.json` exits 0 with `mismatch_count=0`.
  - [ ] `uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_mismatch.json` exits nonzero or reports `trading_halted=true`.

  **QA Scenarios**:
  ```
  Scenario: Reconciliation detects position drift
    Tool: bash
    Steps: uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_mismatch.json | tee .omo/evidence/task-26-reconcile-mismatch.txt
    Expected: output includes POSITION_MISMATCH and apply=false
    Evidence: .omo/evidence/task-26-reconcile-mismatch.txt

  Scenario: Startup recovery blocks unsafe run
    Tool: bash
    Steps: uv run nfi-engine preflight check --profile bybit-testnet --config tests/fixtures/config/reconcile-required.yaml 2>&1 | tee .omo/evidence/task-26-startup-recovery-block.txt
    Expected: command exits nonzero and output includes RECONCILIATION_REQUIRED
    Evidence: .omo/evidence/task-26-startup-recovery-block.txt
  ```

  **Commit**: YES | Message: `feat(exchange): add reconciliation and recovery checks` | Files: `src/nfi_engine/reconciliation/**`, `src/nfi_engine/exchange/**`, `src/nfi_engine/preflight/**`, `tests/unit/reconciliation/**`, `tests/e2e/test_reconcile_cli.py`, `tests/fixtures/exchange/**`

- [x] 27. Add Pairlist Management And Market Eligibility UI

  **What to do**: Add pairlist service for whitelist, blacklist, quote/settle filtering, liquidity threshold, volatility threshold, futures eligibility, leverage eligibility, exchange market availability, and deterministic pair ordering. Add CLI, REST, and simple frontend controls for editing whitelist/blacklist and previewing rejected pairs with reasons.
  **Must NOT do**: Do not download live market data in tests. Do not silently trade pairs rejected by pairlist validation. Do not make pairlist UI a performance dashboard.

  **Parallelization**: Can Parallel: YES | Wave 6 | Blocks: Tasks 29, 30 | Blocked By: Tasks 3, 5, 9, 11, 13, 15, 17, 22, 23

  **References**:
  - Pattern: `src/nfi_engine/data/**` from Task 5 - fixture candles and market data loading.
  - Pattern: `src/nfi_engine/exchange/**` from Task 9 - market metadata.
  - Pattern: `src/nfi_engine/ui/**` from Task 22 - compact frontend controls.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/pairlist tests/e2e/test_pairlist_cli.py tests/e2e/test_pairlist_ui.py -q` covers whitelist, blacklist, liquidity filter, volatility filter, futures eligibility, unsupported pair rejection, deterministic ordering, frontend edit preview, and apply audit event.
  - [ ] `uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/task-27-pairlist.json` exits 0 and writes accepted/rejected pairs with reasons.
  - [ ] Browser QA can add a pair to blacklist, preview rejection reason, save draft, and see audit event.

  **QA Scenarios**:
  ```
  Scenario: Pairlist validation reports rejected pairs
    Tool: bash
    Steps: uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/task-27-pairlist.json && python3 -m json.tool .omo/evidence/task-27-pairlist.json | tee .omo/evidence/task-27-pairlist.txt
    Expected: output includes accepted_pairs, rejected_pairs, and rejection reason codes
    Evidence: .omo/evidence/task-27-pairlist.json

  Scenario: Pairlist UI edits blacklist safely
    Tool: browser/Playwright
    Steps: start API; open http://127.0.0.1:18080/settings; open Pairlist section; add DOGE/USDT to blacklist; click Preview; click Save draft; capture screenshot to .omo/evidence/task-27-pairlist-ui.png
    Expected: UI shows DOGE/USDT rejected by blacklist and no bot restart occurs without explicit apply
    Evidence: .omo/evidence/task-27-pairlist-ui.png
  ```

  **Commit**: YES | Message: `feat(pairlist): add market eligibility controls` | Files: `src/nfi_engine/pairlist/**`, `src/nfi_engine/api/**`, `src/nfi_engine/ui/**`, `tests/unit/pairlist/**`, `tests/e2e/test_pairlist_cli.py`, `tests/e2e/test_pairlist_ui.py`

- [x] 28. Enhance Execution Simulator With Realistic Fill Models

  **What to do**: Extend simulator/backtest/paper execution with configurable partial fills, order latency, maker/taker fee selection, funding fee accrual, abnormal slippage, exchange rejects, liquidation near-miss events, and deterministic random seeds. Add scenario fixtures and make output metadata record scenario hash and seed.
  **Must NOT do**: Do not claim exact live-exchange fidelity. Do not introduce non-deterministic tests. Do not change baseline deterministic backtest behavior unless a simulator scenario explicitly enables the enhanced model.

  **Parallelization**: Can Parallel: YES | Wave 5 | Blocks: Task 30 | Blocked By: Tasks 2, 5, 6, 8, 9, 18, 19

  **References**:
  - Pattern: `src/nfi_engine/backtest/**` from Tasks 6 and 18 - deterministic outputs and metadata.
  - Pattern: `src/nfi_engine/exchange/**` from Task 9 - simulator adapter.
  - Pattern: `src/nfi_engine/circuit_breakers/**` from Task 19 - slippage/funding/liquidation safety events.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/exchange tests/unit/backtest tests/e2e/test_simulator_scenarios.py -q` covers partial fill, latency, funding fee, slippage spike, exchange reject, liquidation near-miss, deterministic seed, and baseline unchanged behavior.
  - [ ] `uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/task-28-fill-sim.json` exits 0 and writes scenario_hash and seed.
  - [ ] Backtest output records simulator scenario metadata only when enhanced fill model is enabled.

  **QA Scenarios**:
  ```
  Scenario: Partial-fill scenario is deterministic
    Tool: bash
    Steps: uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/task-28-fill-sim-a.json && uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/task-28-fill-sim-b.json && cmp .omo/evidence/task-28-fill-sim-a.json .omo/evidence/task-28-fill-sim-b.json | tee .omo/evidence/task-28-fill-sim-deterministic.txt
    Expected: cmp exits 0 and outputs are identical
    Evidence: .omo/evidence/task-28-fill-sim-a.json, .omo/evidence/task-28-fill-sim-deterministic.txt

  Scenario: Slippage spike triggers safety event
    Tool: bash
    Steps: uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/slippage_spike.yaml --output .omo/evidence/task-28-slippage.json 2>&1 | tee .omo/evidence/task-28-slippage.txt
    Expected: output or JSON includes SLIPPAGE_ANOMALY and circuit_breaker_event=true
    Evidence: .omo/evidence/task-28-slippage.json
  ```

  **Commit**: YES | Message: `feat(simulator): model realistic execution scenarios` | Files: `src/nfi_engine/exchange/**`, `src/nfi_engine/backtest/**`, `tests/unit/exchange/**`, `tests/e2e/test_simulator_scenarios.py`, `tests/fixtures/simulator/**`

- [x] 29. Add Frontend Security And Read-Only Access Controls

  **What to do**: Add frontend/session security for local operator console: authenticated session cookie, CSRF token on mutating UI/API calls, session expiry, logout, read-only mode, role-scoped permissions for settings/logs/backup/pairlist, locked controls for live/dangerous fields, security audit events, and browser-visible reason when an action is disabled.
  **Must NOT do**: Do not rely on frontend-only checks. Do not store tokens in localStorage. Do not allow read-only mode to mutate config, backups, pairlists, or runtime state. Do not reveal secrets in disabled-control tooltips or audit events.

  **Parallelization**: Can Parallel: YES | Wave 6 | Blocks: Task 30 and Final Verification | Blocked By: Tasks 11, 15, 16, 21, 22, 23, 24, 25, 27

  **References**:
  - Pattern: `src/nfi_engine/api/**` from Task 11 - auth boundary.
  - Pattern: `src/nfi_engine/safety/**` from Task 15 - safety gates and local-only defaults.
  - Pattern: `src/nfi_engine/ui/**` from Tasks 22 and 27 - settings/logs/pairlist frontend.

  **Acceptance Criteria**:
  - [ ] `uv run pytest tests/unit/api tests/unit/ui tests/e2e/test_frontend_security.py -q` covers session login, session expiry, CSRF rejection, read-only setting mutation rejection, read-only backup restore rejection, read-only pairlist mutation rejection, locked live controls, logout, and audit events.
  - [ ] Mutating UI endpoints reject missing/invalid CSRF token with typed error code.
  - [ ] Browser QA proves read-only mode can inspect settings/logs/pairlists but cannot save/apply/restore/start/stop.

  **QA Scenarios**:
  ```
  Scenario: CSRF blocks mutating settings request
    Tool: HTTP call
    Steps: start API; curl -i -X POST -H 'Authorization: Bearer test-token' http://127.0.0.1:18080/api/v1/config/apply | tee .omo/evidence/task-29-csrf-reject.txt
    Expected: response status is 403 and body includes CSRF_TOKEN_REQUIRED
    Evidence: .omo/evidence/task-29-csrf-reject.txt

  Scenario: Read-only UI cannot mutate configuration
    Tool: browser/Playwright
    Steps: start API with readonly-debug profile; open http://127.0.0.1:18080/settings; verify Save/Apply/Restore controls are disabled with reason; attempt direct UI action; capture screenshot to .omo/evidence/task-29-readonly-ui.png
    Expected: UI allows inspection only and audit log records READONLY_ACTION_BLOCKED
    Evidence: .omo/evidence/task-29-readonly-ui.png
  ```

  **Commit**: YES | Message: `feat(ui): harden operator console access controls` | Files: `src/nfi_engine/api/**`, `src/nfi_engine/ui/**`, `src/nfi_engine/safety/**`, `tests/unit/ui/**`, `tests/e2e/test_frontend_security.py`

- [x] 30. Add Documentation, Evidence Harness, And CI-Like Gates

  **What to do**: Add README with original project identity, clean-room disclaimer, setup, Docker/Compose quickstart, commands, examples, architecture map, module boundaries, frontend operator console usage, profiles/preflight workflow, migrations/version history, backup/restore, diagnostics, exchange reconciliation, pairlist management, realistic simulator scenarios, frontend security controls, QA workflow, and first-milestone limitations. Add `justfile` or scripts for evidence capture if project chooses a task runner; otherwise document exact `uv run` and `docker compose` commands. Add optional GitHub Actions workflow if repo is initialized.
  **Must NOT do**: Do not market the engine as Freqtrade or official NFI. Do not include profit claims. Do not document unsafe live-trading shortcuts.

  **Parallelization**: Can Parallel: YES | Wave 6 | Blocks: Final Verification | Blocked By: Tasks 12, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29

  **References**:
  - Pattern: `.omo/plans/nfi-engine.md` Scope boundaries, Docker task, plugin task, reproducibility task, circuit breaker task, notification task, sandbox task, frontend console task, profiles/preflight task, migration task, backup task, reconciliation task, pairlist task, simulator task, and frontend security task - final docs must preserve clean-room, no-live-trading, local-only container defaults, reproducibility, simple UI, logs/reporting, dry-run-first maintenance, and safety guarantees.
  - External: `https://github.com/freqtrade/freqtrade` - feature benchmark and disclaimer style, do not copy wording.

  **Acceptance Criteria**:
  - [ ] `uv run pytest -q` exits 0.
  - [ ] `uv run ruff format --check . && uv run ruff check . && uv run basedpyright` exits 0.
  - [ ] README includes setup, Docker quickstart, dry-run warning, clean-room note, architecture modules, plugin model, reproducible backtest metadata, walk-forward validation, circuit breakers, notifications, sandboxing, frontend settings/logs console, profiles/preflight, migrations/version history, backup/restore, diagnostics, reconciliation, pairlist, simulator scenarios, frontend security, error-code reporting workflow, and command examples.
  - [ ] `docs/docker.md` explains image build, Compose profiles, local-only port binding, volumes, secret handling, and teardown.
  - [ ] `docs/plugins.md`, `docs/reproducibility.md`, `docs/circuit-breakers.md`, `docs/notifications.md`, `docs/sandbox.md`, `docs/ui.md`, `docs/operations.md`, `docs/backup.md`, `docs/reconciliation.md`, `docs/pairlist.md`, and `docs/simulator.md` explain operator usage and limitations.
  - [ ] Evidence harness can run final smoke commands and write `.omo/evidence/final-*` files.

  **QA Scenarios**:
  ```
  Scenario: Full quality gate passes
    Tool: bash
    Steps: uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest -q | tee .omo/evidence/task-30-full-gate.txt
    Expected: all commands exit 0
    Evidence: .omo/evidence/task-30-full-gate.txt

  Scenario: README quickstart commands are executable
    Tool: tmux
    Steps: tmux new-session -d -s ulw-qa-task30 'cd /home/user/nfi_engine && uv run nfi-engine config validate --config examples/spot-paper.yaml && uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml && uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/task-30-readme-backtest.json'; sleep 8; tmux capture-pane -pt ulw-qa-task30 -S -500 > .omo/evidence/task-30-readme-quickstart.txt; tmux kill-session -t ulw-qa-task30
    Expected: transcript contains successful config validation, preflight check, and backtest output path
    Evidence: .omo/evidence/task-30-readme-quickstart.txt

  Scenario: Docker quickstart command is documented and runnable
    Tool: bash
    Steps: docker compose config >/tmp/nfi-engine-compose-config.txt && docker compose --profile paper run --rm cli nfi-engine --help | tee .omo/evidence/task-30-docker-quickstart.txt
    Expected: compose config exits 0 and CLI help includes nfi-engine
    Evidence: .omo/evidence/task-30-docker-quickstart.txt
  ```

  **Commit**: YES | Message: `docs(project): document nfi engine milestone workflow` | Files: `README.md`, `docs/**`, `.github/workflows/**`, `.omo/evidence/**`

## Final Verification Wave (MANDATORY - after ALL implementation tasks)
> ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
- [x] F1. Plan Compliance Audit
  - Verify every TODO acceptance criterion has matching current evidence.
  - Command: `python3 scripts/verify_plan_evidence.py .omo/plans/nfi-engine.md .omo/evidence`
  - Evidence: `.omo/evidence/final-plan-compliance.txt`
- [x] F2. Code Quality Review
  - Command: `uv run ruff format --check . && uv run ruff check . && uv run basedpyright && uv run pytest -q`
  - Evidence: `.omo/evidence/final-quality-gate.txt`
- [x] F3. Real Manual QA
  - CLI: `uv run nfi-engine --help`
  - Config: `uv run nfi-engine config validate --config examples/futures-paper.yaml`
  - Backtest: `uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/final-backtest.json`
  - Walk-forward: `uv run nfi-engine validate walk-forward --config examples/spot-paper.yaml --splits 3 --output .omo/evidence/final-walk-forward.json`
  - Paper: `uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 25`
  - Plugins: `uv run nfi-engine plugins list --config examples/futures-paper.yaml`
  - Circuit breaker: `uv run nfi-engine circuit-breaker simulate --config tests/fixtures/config/daily-loss-limit.yaml`
  - Notification: `uv run nfi-engine notify test --config examples/futures-paper.yaml --channel jsonl --message final-smoke --output .omo/evidence/final-notify.jsonl`
  - Sandbox: `uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.unsafe:EnvReadingStrategy`
  - Profiles: `uv run nfi-engine profile list | tee .omo/evidence/final-profile-list.txt`
  - Preflight: `uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml | tee .omo/evidence/final-preflight.txt`
  - DB migration dry-run: `uv run nfi-engine db migrate --dry-run --database tests/fixtures/db/v0.sqlite | tee .omo/evidence/final-db-migrate.txt`
  - Config migration dry-run: `uv run nfi-engine config migrate --dry-run --config tests/fixtures/config/v0-config.yaml | tee .omo/evidence/final-config-migrate.txt`
  - Backup: `uv run nfi-engine backup create --config examples/futures-paper.yaml --output .omo/evidence/final-backup.zip`, then `uv run nfi-engine backup verify .omo/evidence/final-backup.zip | tee .omo/evidence/final-backup-verify.txt`
  - Restore dry-run: `uv run nfi-engine backup restore --dry-run .omo/evidence/final-backup.zip | tee .omo/evidence/final-restore-dry-run.txt`
  - Reconciliation: `uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_mismatch.json | tee .omo/evidence/final-reconcile.txt`
  - Pairlist: `uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/final-pairlist.json`
  - Fill simulator: `uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/final-fill-sim.json`
  - REST: start API on `127.0.0.1:18080`, then `curl -i http://127.0.0.1:18080/api/v1/ping`
  - Frontend settings: browser opens `http://127.0.0.1:18080/settings`, edits a safe setting, validates it, saves a draft, applies/reloads when allowed, and captures `.omo/evidence/final-settings-ui.png`
  - Frontend logs/report: browser opens `http://127.0.0.1:18080/logs`, filters an error code, views correlation ID/report hint, exports `.omo/evidence/final-support-report.zip`, and captures `.omo/evidence/final-logs-ui.png`
  - Frontend pairlist/security: browser opens `http://127.0.0.1:18080/settings`, previews pairlist rejection, verifies read-only mode disables mutating controls, and captures `.omo/evidence/final-readonly-ui.png`
  - Frontend CSRF: `curl -i -X POST -H 'Authorization: Bearer test-token' http://127.0.0.1:18080/api/v1/config/apply | tee .omo/evidence/final-csrf-reject.txt`
  - Docker image: `docker build -t nfi-engine:local .`
  - Docker REST: `docker compose --profile paper up --build -d api`, then `curl -i http://127.0.0.1:18080/api/v1/ping`, then `docker compose down -v`
  - Docker CLI: `docker compose run --rm cli nfi-engine config validate --config /app/examples/futures-paper.yaml`
  - Evidence: `.omo/evidence/final-manual-qa.txt`, `.omo/evidence/final-api-ping.txt`, `.omo/evidence/final-backtest.json`, `.omo/evidence/final-walk-forward.json`, `.omo/evidence/final-plugins.txt`, `.omo/evidence/final-circuit-breaker.txt`, `.omo/evidence/final-notify.jsonl`, `.omo/evidence/final-sandbox.txt`, `.omo/evidence/final-profile-list.txt`, `.omo/evidence/final-preflight.txt`, `.omo/evidence/final-db-migrate.txt`, `.omo/evidence/final-config-migrate.txt`, `.omo/evidence/final-backup.zip`, `.omo/evidence/final-backup-verify.txt`, `.omo/evidence/final-restore-dry-run.txt`, `.omo/evidence/final-reconcile.txt`, `.omo/evidence/final-pairlist.json`, `.omo/evidence/final-fill-sim.json`, `.omo/evidence/final-settings-ui.png`, `.omo/evidence/final-logs-ui.png`, `.omo/evidence/final-support-report.zip`, `.omo/evidence/final-readonly-ui.png`, `.omo/evidence/final-csrf-reject.txt`, `.omo/evidence/final-docker-build.txt`, `.omo/evidence/final-docker-ping.txt`, `.omo/evidence/final-docker-cli.txt`
- [x] F4. Scope Fidelity Check
  - Verify no copied Freqtrade/NFI source or UI design files.
  - Verify no real exchange keys and no live real-order pathway enabled by default.
  - Verify Docker image and Compose config do not include secrets, runtime DBs, logs, `.git`, `.omo/evidence`, caches, or root runtime user.
  - Verify Compose ports bind to `127.0.0.1`, not `0.0.0.0`.
  - Verify plugins cannot load from unconfigured roots and cannot import before manifest validation.
  - Verify backtest reports include config/data/strategy/engine/dependency hashes.
  - Verify circuit breakers block new order intents before exchange placement.
  - Verify notifier failures are non-fatal and redact secrets.
  - Verify sandbox blocks unsafe strategy capability access while allowing NFI-shaped fixtures.
  - Verify frontend settings cannot bypass safety gates, reveal secrets, or make live trading available.
  - Verify frontend log/report workflow includes error code, correlation ID, redacted summary, and support bundle without sensitive values.
  - Verify profiles/preflight block unsafe starts before paper or testnet execution.
  - Verify migrations, config rollback, backup restore, and exchange reconciliation all have dry-run/preview paths before mutation.
  - Verify backup and diagnostic archives contain no secrets, `.env`, `.git`, caches, raw tokens, or unredacted logs.
  - Verify exchange reconciliation reports drift without mutating local DB or exchange state in milestone 1.
  - Verify pairlist validation blocks rejected pairs before strategy signals can create order intents.
  - Verify realistic simulator scenarios are deterministic by seed and clearly labeled as approximations.
  - Verify frontend CSRF, session expiry, read-only mode, and locked dangerous controls work through API and browser QA.
  - Verify all source files are at or below 250 pure LOC or have been split.
  - Evidence: `.omo/evidence/final-scope-fidelity.txt`

## Commit Strategy
- Do not auto-commit unless the user explicitly authorizes commits.
- Keep each task as one logical commit when authorized.
- Use Conventional Commit subjects listed in each task.
- If commits are created, include plan footer:
  `Plan: .omo/plans/nfi-engine.md`
- Never commit secrets or generated DB files.
- Evidence files under `.omo/evidence/` can be committed only if the user wants reproducible QA artifacts in git; otherwise leave them untracked.

## Success Criteria
- The repository is initialized as a strict Python package.
- All implementation tasks are complete with RED->GREEN evidence.
- The engine supports spot and futures domain semantics.
- Backtest and paper-run work through the CLI.
- Backtest output is reproducible by config, strategy, data, engine, and dependency hashes.
- Walk-forward validation produces split-level and aggregate metrics.
- REST API exposes local control/status endpoints and `/api/v1/ping`.
- Simple local frontend lets an operator adjust safe settings, validate/apply/reload config, inspect logs/error codes, and export a redacted support report bundle.
- Operator profiles and preflight checks make start readiness obvious before paper/testnet execution.
- DB/config migrations, config history, rollback preview, backup creation, backup verification, and restore dry-run are available and redacted.
- Exchange reconciliation detects local-vs-exchange order, position, balance, leverage, and lock drift without mutating state by default.
- Pairlist management validates whitelist, blacklist, liquidity, volatility, futures eligibility, and rejected-pair reasons through CLI and frontend.
- Enhanced simulator can model deterministic partial fills, latency, funding, slippage spikes, rejects, and liquidation near-misses.
- Frontend security enforces authenticated sessions, CSRF protection, read-only mode, session expiry, and locked dangerous controls.
- Docker image builds, Compose API responds on local-only `127.0.0.1`, and Compose CLI can validate futures config.
- Plugin registry lists typed strategy, exchange, risk, notifier, and data plugin groups with safe discovery.
- Strategy adapter can run NFI-shaped fixture strategies and reports unsupported full-X7 surfaces honestly.
- Strategy sandbox blocks unsafe filesystem, network, env, subprocess, and direct live-order capability access.
- Simulator and Bybit testnet adapter seam exist; live real-money orders remain disabled.
- SQLite persistence records bot/trade/order/position state.
- Circuit breakers halt new order intents for loss, drawdown, stale data, API error, slippage, funding, and manual halt conditions.
- Notification adapters can emit local JSONL smoke events and handle webhook failure without blocking the engine.
- Safety guardrails prevent weak API auth, public bind defaults, secret leakage, and live trading by default.
- Container guardrails prevent root runtime, baked secrets, public port exposure, and dirty build context inclusion.
- No GPL source/design copying is present.
- Final quality gate passes.
- Final manual QA artifacts exist and prove the real CLI/REST surfaces.
