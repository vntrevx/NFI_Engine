# Operator Console

The milestone 1 console is a local FastAPI-served operator surface at
`/settings` and `/logs`. It is built for simple configuration and diagnostics,
not public analytics.

Milestone 2 expands this into an original operator command center. The home
surface should show setup readiness, safety state, dashboard snapshots, local
chart status, recent errors, and support actions without imitating FreqUI.

## Home

`/` is the first operator screen. It shows runtime state, exchange mode,
open-trade and PnL placeholders, setup readiness, safety blocking reasons, a
pairlist preview, recent error codes, and a support report shortcut.

First-run operators should be able to decide three things from Home without
opening YAML:

- whether setup is complete enough to run paper or testnet workflows
- whether safety gates are blocking a live-risk action
- whether recent errors need a support report

## Language Selector

The console supports English, Korean, and Greek. M2 keeps language selection
explicit through config or supported route/session controls; it does not guess
from browser locale. Machine codes, audit event IDs, and API contract tokens
remain untranslated so support reports stay searchable.

## Dashboard Chart

The home chart is a local canvas renderer with no external chart library. It
polls `GET /api/v1/dashboard/snapshot` every 5 seconds, aborts a refresh after
2.5 seconds, and marks the chart stale after 15 seconds without a successful
snapshot. The footer reports render time and response payload bytes so local QA
can catch wasteful polling or payload growth early.

Expected states:

- `loading`: a snapshot request is in flight
- `ready`: at least one price or equity point rendered
- `empty`: the snapshot is valid but has no chart points yet
- `stale`: previous data exists but refreshes are no longer current
- `error`: no usable snapshot could be rendered

## Settings

`/settings` renders editable fields from config metadata, hides sensitive
fields, blocks live-trading controls, and sends typed field patches to the API.
Runtime-safe fields can be validated, saved as a draft, and applied without
editing raw YAML.

Simple Mode is the default first-run editing surface. It keeps exchange, trading
mode, paper/testnet intent, stake sizing, risk preset, locale, and write-only
credential entry visible. The setup preview uses `/api/v1/setup/preview` and
returns redacted config text; credential values are not written into HTML values,
browser storage, logs, or support reports. Advanced Mode stays collapsed for
later tuning.

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
- M2 dashboard work must keep its own navigation, layout, text, and chart
  treatment; Freqtrade is only a behavior reference.
