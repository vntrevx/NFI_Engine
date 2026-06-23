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
runtime health snapshot, wallet balance state, a pairlist preview, recent error
codes, an operator cockpit, and a support report shortcut.

First-run operators should be able to decide three things from Home without
opening YAML:

- whether setup is complete enough to run paper or testnet workflows
- whether safety gates are blocking a live-risk action
- whether recent errors need a support report

The operator cockpit compresses the first-run decision state into one panel:
configured or missing credentials, dry-run safe or blocked, exchange capability
level, active mode, runtime health, wallet balance state, allocated amount,
leverage, latest error, next action, and where to go next. It is rendered from
typed settings, preflight, logs, dashboard action data, and runtime health data;
it does not read browser storage or raw config dictionaries.

## Runtime Health And Wallet Fetch

Detailed runtime health is exposed through protected local JSON at
`GET /api/v1/runtime/health`. It reports one operator state:
`healthy`, `degraded`, or `blocked`, with a next action and typed checks for
heartbeat, preflight, wallet balance, stale dashboard data, manual halt,
disk budget, and memory budget.

Wallet balance reads stay behind the exchange adapter boundary. Settings uses
an explicit operator action, `POST /api/v1/wallet/balance/fetch`, and Home only
renders the latest typed wallet state. The UI does not fetch wallet balance on
page load, does not run a wallet polling timer, and does not store wallet data,
API keys, bearer tokens, or CSRF tokens in browser storage.

## Runtime Controls

Home and Settings expose the same protected runtime controls:

- `POST /api/v1/start`
- `POST /api/v1/pause`
- `POST /api/v1/resume`
- `POST /api/v1/stop`
- `GET` / `POST /api/v1/runtime/control`

Pause blocks new entries while keeping state inspectable. Resume requires
preflight and runtime health to allow entries again. Stop moves the local runtime
state toward stopped and does not claim to cancel live exchange orders. The
generic `/runtime/control` endpoint returns stable machine codes for malformed
commands, repeated pause/stop, blocked health, blocked preflight, read-only
mode, and live-unsafe intent.

The browser script refreshes runtime state on page load and after each command.
It does not poll continuously, does not store runtime state in browser storage,
and reads CSRF only from the page meta tag. Server-side write protection remains
the real gate: CSRF, authenticated session, read-only mode, live-mode safety,
preflight, runtime health, and circuit-breaker checks all stay on the API side.

## Action Queue

M2.5 adds a compact action queue to Home and to
`GET /api/v1/dashboard/snapshot`. It is a bounded next-action list, not a
general task system. The queue is built from data already available to the
dashboard snapshot: preflight readiness, recent safe error summaries, configured
pairlist state, and paper/testnet safety state.

The queue returns at most four actions. Current action targets are:

- `settings/setup`: setup or preflight issue; Home links to `/settings`
- `logs`: recent runtime errors; Home links to `/logs`
- `settings`: pairlist/config issue; Home links to `/settings`
- `dashboard/status`: safe ready state; Home links to the status strip
- `logs/support-bundle`: support follow-up; Home links directly to
  `/api/v1/reports/support-bundle.zip`

The Home queue must stay cheap for low-resource machines: no extra polling loop,
no UI storage access, no repeated full-config parse, no database read from the
UI renderer, and no live-order shortcut.

## Language Selector

The console supports English, Korean, and Greek. M2 keeps language selection
explicit through config or supported route/session controls; it does not guess
from browser locale. Machine codes, audit event IDs, and API contract tokens
remain untranslated so support reports stay searchable.

When the operator changes `ui.locale` in Settings and presses Apply, the page
uses the runtime-safe config API and reloads itself. The operator should not
need to press F5 manually.

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

The first-run setup wizard is the default operator path. It renders this order:
exchange, exchange API key, exchange API secret, recommended leverage `3x`,
API permission audit, risk profile, wallet balance fetch button/state, allocated
amount, futures/spot, and dry-run/live. Dry-run is selected by default. Live remains
visibly gated and setup preview returns `LIVE_TRADING_REQUIRES_CONFIRMATION`
until the explicit live confirmation path exists.

The API permission audit uses short operator labels for read, trade, futures,
withdrawal, and IP allowlist status. Withdrawal-like permission blocks live
setup; unknown permission remains previewable for dry-run/testnet diagnostics.
Risk profiles are `safe`, `balanced`, and `expert`; `balanced` keeps the 3x
default path, while `expert` requires explicit confirmation before setup or
preflight can pass.

Simple Mode remains available for everyday runtime-safe edits. It keeps exchange,
trading mode, locale, stake sizing, and max open trades visible. The setup
preview uses `/api/v1/setup/preview` and returns redacted config text; credential
values are not written into HTML values, browser storage, logs, or support
reports. Advanced Mode stays collapsed for later tuning.

Settings also shows a developer update panel for engine + strategy update state.
Preview, apply, and rollback stay local-only and proof-only: the browser calls
protected local endpoints, receives provenance/backup receipts, and never pulls
from a remote source or mutates runtime config. Apply and rollback require a
backup reference, and unverified provenance stays visibly blocked unless the
operator explicitly acknowledges the local proof gap.

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

## Browser QA Gate

T10 adds a real loopback browser QA command for the operator console:

```bash
npm install
npm run nfi:browser-qa:deps
npm run nfi:browser-qa
```

The command starts a QA-only `uv run nfi-engine serve` process on
`127.0.0.1:<free-port>`, drives Chromium through login, Home, Settings locale
apply, Logs, desktop capture, and mobile capture, then writes evidence under
`.omo/evidence/2026-06-15-product-completion/task-10-browser/`.

For T14 first-run QA, the same command is run with
`NFI_BROWSER_QA_EVIDENCE_DIR=.omo/evidence/2026-06-15-product-completion/task-14-browser`
and verifies the setup wizard order, dry-run default, 3x recommendation, Home
operator cockpit, update preview/apply/rollback states, secret redaction, live
gate, local-only network, empty browser storage, and mobile overflow.

For T22 credential/risk QA, the loopback browser evidence under
`.omo/evidence/2026-06-15-product-completion/task-22-browser/` verifies Home and
Settings show API permission audit and risk profile state, language apply works
for EN/KO/EL without manual F5, browser storage stays empty, external requests
stay at zero, and desktop/mobile layouts avoid horizontal overflow.

For T23 wallet/runtime health QA, the loopback evidence under
`.omo/evidence/2026-06-15-product-completion/task-23-*` verifies explicit wallet
fetch through `POST /api/v1/wallet/balance/fetch`, Home runtime health and
wallet state, missing-credential blockers, no external browser requests, empty
browser storage, and desktop/mobile layouts without horizontal overflow. The
runtime-control follow-up evidence under
`.omo/evidence/2026-06-15-product-completion/task-23-runtime-control-*` verifies
Home and Settings start/pause/resume/stop behavior without manual refresh,
CSRF/read-only/live-unsafe/blocked-health denials, empty browser storage,
loopback-only network requests, and desktop/mobile layouts without horizontal
overflow.

For T25 operator visual/i18n QA:

```bash
npm run nfi:browser-qa:wp9
```

The command drives the current loopback UI through login, EN/KO/EL language
switching without manual F5, Home, Settings, Logs, setup, wallet fetch, update
preview/apply/rollback states, data lifecycle controls, pairlist controls,
runtime health/control reads, support bundle export, and desktop/mobile
captures. Evidence is written under
`.omo/evidence/2026-06-17-product-completion/wp9/browser/`.

The WP9 gate also checks that browser storage stays empty, network requests stay
loopback-local, console errors stay empty, generated tokens do not appear in
evidence, machine codes remain searchable, and Korean/Greek captures have no
body horizontal overflow, clipped text, incoherent overlap, or missing glyphs.

The gate fails if:

- any request is not loopback-local
- the generated QA token appears in screenshots or JSON evidence
- browser `localStorage` or `sessionStorage` contains entries after login
- an unexpected console error appears
- mobile captures show horizontal page overflow

`npm run nfi:browser-qa:deps` prepares rootless local Chromium runtime
libraries and Noto CJK fonts under ignored `.omo/tools/browser-libs/` when the
host image lacks them.

## Read-Only Mode

Set `ui.read_only: true` to allow inspection while blocking mutation:

- can inspect settings
- can inspect logs and support report metadata
- can preview pairlist eligibility
- cannot save/apply config
- cannot apply pairlist drafts
- cannot restore backups
- cannot start/pause/resume/stop runtime state

Read-only is enforced on the server. Disabled buttons are only the visible
operator hint.

## Limits

- Local-only by default.
- No external CDN assets.
- No broad trading dashboard in M1.
- No live-money controls.
- M2 dashboard work must keep its own navigation, layout, text, and chart
  treatment; Freqtrade is only a behavior reference.
