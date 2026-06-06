# Operations

This page covers the M1 operator workflow from config to diagnostics.

## Profiles And Preflight

```bash
uv run nfi-engine profile list
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml
```

Preflight checks config validity, profile compatibility, local API binding,
database/log paths, notifier dry-run readiness, pairlist validity, Docker volume
shape, and exchange/testnet safety rules.

## Config Inspection

```bash
uv run nfi-engine config validate --config examples/futures-paper.yaml
uv run nfi-engine config show --config examples/futures-paper.yaml
uv run nfi-engine config schema --config examples/futures-paper.yaml
```

Config output redacts secrets. Runtime-safe fields can also be edited through
`/settings`.

## Migrations And Version History

```bash
uv run nfi-engine db migrate --dry-run --database tests/fixtures/db/v0.sqlite
uv run nfi-engine config migrate --dry-run --config tests/fixtures/config/v0-config.yaml
uv run nfi-engine config history --config examples/futures-paper.yaml
uv run nfi-engine config rollback --dry-run --to-version previous --config examples/futures-paper.yaml
```

Rollback requires a backup for mutating operations. Keep dry-run transcripts in
`.omo/evidence/` before changing local state.

## Diagnostics

```bash
uv run nfi-engine logs explain CONFIG_VALIDATION_ERROR --events tests/fixtures/events/config_validation_error.jsonl
```

The API exposes `/api/v1/logs/recent`, `/api/v1/errors/{code}`, and
`/api/v1/reports/support-bundle.zip` for the UI.

## First Response For Errors

1. Capture the exact command or route.
2. Capture the typed error code.
3. Capture the correlation ID when available.
4. Export a support report from `/logs`.
5. Reproduce with a fixture or dry-run command before patching.
