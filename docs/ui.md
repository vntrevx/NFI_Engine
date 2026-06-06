# Operator Console

The milestone 1 console is a local FastAPI-served operator surface at
`/settings` and `/logs`. It is built for simple configuration and diagnostics,
not public analytics.

## Settings

`/settings` renders editable fields from config metadata, hides sensitive
fields, blocks live-trading controls, and sends typed field patches to the API.
Runtime-safe fields can be validated, saved as a draft, and applied without
editing raw YAML.

Useful flows:

```bash
uv run nfi-engine serve --config examples/futures-paper.yaml --host 127.0.0.1 --port 18080
```

Open `http://127.0.0.1:18080/settings`.

The page includes:

- runtime-safe settings form
- validate, save draft, and apply controls
- readiness/preflight summary
- pairlist preview and apply controls
- safety-gate lock messages
- read-only reason panel when enabled

## Logs And Reports

`/logs` shows recent operator events, severity filtering, error-code lookup,
correlation IDs, safe summaries, and a zip support report export. Support
reports contain redacted config and recent logs only.

Error-code reporting workflow:

1. Open `/logs`.
2. Filter by severity or look up a known error code.
3. Copy the code, correlation ID, and safe summary.
4. Export the support report zip.
5. Attach the report to a maintenance ticket without adding secrets.

## Security

When an API token is configured, `/settings`, `/logs`, and protected API routes
require an authenticated operator session. Login returns a session cookie and a
CSRF token. Browser pages embed the CSRF token as a meta value and JavaScript
sends it as `x-nfi-csrf-token` on mutating calls.

Server-side write routes require all of:

- authenticated session or bearer authentication at the API boundary
- valid session cookie for CSRF validation
- matching `x-nfi-csrf-token`
- non-read-only UI mode

Missing CSRF returns `CSRF_TOKEN_REQUIRED`. Invalid CSRF returns
`CSRF_TOKEN_INVALID`. Read-only mutation attempts return
`READONLY_ACTION_BLOCKED` and are written to the protected security audit log.

The UI must not store bearer tokens in `localStorage` or `sessionStorage`.

## Read-Only Mode

Set `ui.read_only: true` to allow inspection while blocking mutation:

- can inspect settings
- can inspect logs and support report metadata
- can preview pairlist eligibility
- cannot save/apply config
- cannot apply pairlist drafts
- cannot restore backups
- cannot start/stop runtime state

Read-only is enforced on the server. Disabled buttons are only the visible
operator hint.

## Limits

- Local-only by default.
- No external CDN assets.
- No broad trading dashboard in M1.
- No live-money controls.
