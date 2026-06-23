# SOURCE PACKAGE GUIDE

## OVERVIEW

`src/nfi_engine` is the engine implementation: CLI, FastAPI, local UI, typed
domain models, trading services, persistence, plugins, safety, and operations.

## STRUCTURE

```text
src/nfi_engine/
|-- cli.py, cli_*.py       # Typer command root and command modules
|-- api/                   # FastAPI contracts, auth, routes, UI adapters
|-- ui/                    # local operator HTML/CSS/JS rendering
|-- config/, domain/       # Pydantic settings and typed trading primitives
|-- backtest/, validation/ # deterministic research surfaces
|-- paper/, exchange/      # paper loop, simulator, testnet adapter boundary
|-- persistence/           # async SQLite storage and repositories
|-- safety/, risk/, circuit_breakers/, preflight/, reconciliation/
|-- plugins/, sandbox/     # extension and strategy capability boundaries
`-- maintenance/, setup/, notifications/, observability/, dashboard/
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| New CLI command | `cli.py`, matching `cli_*.py` | Keep command code thin; delegate to services. |
| Config field | `config/models.py`, `config/loader.py`, `api/models.py` | Add redaction and metadata. |
| Runtime safety | `preflight/`, `safety/`, `circuit_breakers/`, `reconciliation/` | Hard blocks belong in services. |
| Strategy compatibility | `strategy/`, `compat/`, `sandbox/` | Clean-room fixtures only. |
| Operator state | `dashboard/`, `persistence/`, `api/dashboard_routes.py` | Read models should stay bounded. |
| Notifications/logs | `notifications/`, `events/`, `observability/` | Redact secrets before output. |

## CONVENTIONS

- Parse at boundaries: config/API input becomes typed Pydantic/domain objects before service logic.
- Keep services deterministic where possible; inject fixture paths, ticks,
  snapshots, and settings rather than reading globals.
- Safety services must be callable outside the UI. Disabled buttons are only hints, never enforcement.
- Plugin and strategy loading must pass through typed manifests, allowlists, and sandbox checks before execution.
- Notification failures may return structured results, but callers that promise readiness must inspect and surface them.
- Preserve module ownership from `docs/contributing.md`; cross-package features need tests at the boundary.
- New modules should stay small and purpose-named. Split when a file mixes API
  contracts, persistence, rendering, and business rules.

## ANTI-PATTERNS

- Do not pass raw config dictionaries deep into trading, risk, exchange, persistence, or UI code.
- Do not let UI/API routes mutate storage, runtime state, or config without a
  typed service call and an explicit safety path.
- Do not make sandbox, preflight, circuit-breaker, reconciliation, or read-only
  checks optional through caller convenience.
- Do not treat simulator/test fixtures as live-market truth.
- Do not add import-time side effects to plugin, strategy, exchange, or persistence modules.
- Do not suppress strict typing with `type: ignore`; fix the shape or move parsing to the boundary.
