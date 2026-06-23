# PERSISTENCE GUIDE

## OVERVIEW

`persistence` owns async SQLite storage, SQLAlchemy session setup, records,
converters, repository protocols, and bounded repository implementations.

## STRUCTURE

```text
persistence/
|-- session.py                # async engine/session factory
|-- models.py                 # SQLAlchemy table models
|-- records.py                # typed storage records
|-- converters.py             # domain/storage mapping
|-- protocols.py              # repository contracts
`-- repositories/
    |-- state.py              # runtime/dashboard state reads
    `-- trading.py            # orders, trades, positions
```

## WHERE TO LOOK

| Task | Location | Notes |
| --- | --- | --- |
| New stored shape | `models.py`, `records.py`, `converters.py` | Update model, record, and mapping together. |
| Database access | `repositories/` | Keep SQL behind repository methods. |
| Session lifecycle | `session.py` | Async engine/session ownership. |
| Maintenance | `src/nfi_engine/maintenance/` | Migrations, backup, restore, config history. |
| Tests | `tests/integration/persistence`, `tests/unit/maintenance` | Use fixture DBs and temp paths. |

## CONVENTIONS

- API/UI/trading services should call repositories or maintenance services, not raw SQLAlchemy sessions.
- Keep database records typed and explicit; converters bridge storage rows and domain/API read models.
- SQLite is the first storage target, but avoid shapes that make a later Postgres repository impossible.
- Migrations, rollback, restore, reconciliation, and destructive maintenance need dry-run/preview before mutation.
- Backup/support bundles must redact API tokens, exchange credentials, webhook URLs, and secret-bearing config.
- Async tests often pin the `anyio_backend` to `asyncio`; match existing persistence tests.

## ANTI-PATTERNS

- Do not let HTML rendering, route handlers, or CLI glue reach directly into storage rows.
- Do not mix schema migration, repository query, and support-bundle formatting in one module.
- Do not mutate real operator data in tests; use temp directories, fixture DBs, and dry-run paths.
- Do not put runtime SQLite files, generated backups, or support bundles into source-controlled paths.
- Do not hide checksum, tamper, restore, or migration failures behind generic exceptions.
