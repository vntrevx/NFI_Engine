# Freqtrade-Inspired Feature Coverage

NFI Engine uses Freqtrade as a behavior benchmark, not as a source, UI, or
architecture template. This document tracks the broad feature ideas operators
expect from a serious crypto trading bot and records the NFI Engine angle for
each one.

## Clean-Room Boundary

- Do not copy Freqtrade, FreqUI, or NostalgiaForInfinity source code.
- Do not mirror FreqUI navigation, page composition, colors, wording, or chart
  layout.
- Use official documentation and public behavior as the feature reference.
- Keep machine-readable compatibility claims backed by tests and evidence.
- Treat Freqtrade comparison as a black-box benchmark only.

## Roadmap Labels

- `operator-usability`: first-run setup, dashboard clarity, fewer decisions.
- `performance`: measured speed, low allocation pressure, benchmark evidence.
- `safety`: live-trading gates, redaction, circuit breakers, clear blockers.
- `strategy-research`: backtests, validation, strategy adapter compatibility.
- `plugin-ecosystem`: typed extension points and safe plugin discovery.
- `oss-polish`: contributor docs, issue templates, support bundles, roadmap.

## Coverage Matrix

| Feature category | Current status | NFI Engine angle | Labels |
| --- | --- | --- | --- |
| Setup | M2 hardening | One-command Docker install plus guided config generation; the operator should mostly provide exchange mode and keys. The installed login/Home/setup path has browser and HTTP evidence under `.omo/evidence/2026-06-12-dev-entry/`. | `operator-usability`, `safety`, `oss-polish` |
| Configuration | M2 hardening | Simple Mode first, Advanced collapsed, typed patches, no raw YAML as the primary path. Runtime-safe apply mutates running settings; restart-required changes stay explicit. | `operator-usability`, `safety` |
| Bot control | M1 done, M2 hardening | Start/pause/stop stay behind local auth, CSRF, read-only state, and safety explanations. Server-side read-only denial is pinned with HTTP evidence. | `safety`, `operator-usability` |
| REST API | M1 done, M2 hardening | Typed local API with dashboard snapshots and stable machine codes; frontend text can localize without changing contracts. | `operator-usability`, `performance` |
| Logs | M1 done, M2 hardening | Error-code lookup, correlation IDs, and redacted support bundles remain first-class maintenance tools. Mobile table rendering is treated as operator QA, not only route coverage. | `operator-usability`, `oss-polish` |
| Trades | M1 done, M2 expose | Recent trades and open positions feed the home dashboard through bounded read models, not ad hoc row queries. | `performance`, `safety` |
| Locks | M1 done, M2 explain | Pair locks and circuit-breaker blocks get human Safety Explainer text on the home surface. | `safety`, `operator-usability` |
| Pairlists | M1 done, M2 summarize | Pairlist previews stay editable, while the home page shows eligibility health and rejected-pair reasons. | `safety`, `operator-usability` |
| Protections | M1 done, M2 summarize | Protection state should read as operator guidance: why new orders are blocked and how to recover. | `safety` |
| Backtesting | M1 done, M3+ UI | CLI backtests and reproducibility metadata exist; a full backtest UI waits until the dashboard foundation is stable. | `strategy-research`, `performance` |
| Charts | M2 hardening | Local chart MVP uses snapshot polling and render-time evidence before exchange streaming or heavy libraries. | `operator-usability`, `performance` |
| Hyperopt | M3+ backlog | Treat optimization as an evidence workflow with benchmark budgets, not a checklist exercise. | `strategy-research`, `performance` |
| FreqAI | M3+ backlog | Future research layer must be optional, isolated, and benchmarked; no M2 dependency weight. | `strategy-research`, `performance` |
| Notifications | M1 done, M2 surface | Existing notifiers stay adapter-based; the home page can surface notifier health and support-report context. | `operator-usability`, `safety` |
| Webhooks | M1 done | Generic webhook notification is available; M2 keeps it redacted and non-blocking. | `safety`, `oss-polish` |
| Futures | M1 done, M2 setup | Futures mode is supported through typed domain rules and setup guidance, with live execution still gated. | `safety`, `operator-usability` |
| Exchange support | S1 boundary, S4 build | Freqtrade-documented exchanges are recorded as `candidate`; NFI Engine promotes only fixture/testnet/sandbox-backed profiles to `verified`, and broader exchange ids stay `generic-unverified`. See [exchange-support-matrix.md](exchange-support-matrix.md). | `safety`, `operator-usability`, `oss-polish` |
| Strategy callbacks | S2 core contract | Adapter inspection classifies callbacks as `supported`, `partial`, or `excluded`; sandbox can emit a clean-room JSON compatibility report for local strategy specs. Broader runtime parity still waits for signal/protection timeline evidence. | `strategy-research` |
| Data downloading | M3+ backlog | Do not add network-heavy data ingestion to M2; design later around typed datasets and benchmarked loading. | `strategy-research`, `performance` |
| Persistence | M1 done, M2 read models | SQLite repositories remain the source of truth; dashboard paths use bounded list queries. | `performance`, `safety` |
| Backup | M1 done, M2 shortcut | Support Bundle Plus and one-click backup context make maintenance simpler without leaking secrets. | `safety`, `oss-polish` |
| Recovery | M1 done, M2 explain | Restore, migration, reconciliation, and readiness failures should produce actionable operator text. | `safety`, `operator-usability` |
| Plugin ecosystem | M1 done, M3+ gallery | Typed manifests and allowlisted roots exist; a public gallery comes after compatibility and sandbox hardening. | `plugin-ecosystem`, `oss-polish` |
| Performance benchmarks | M2 hardening | Baseline NFI Engine first, optional black-box Freqtrade comparison later, no public speed claim without evidence. `scripts/final_smoke.sh` writes valid local benchmark JSON; `PERFORMANCE_REGRESSION` is required only when a baseline report is supplied. | `performance`, `oss-polish` |

## M2 Scope

M2 closes the usability layer: simple setup, home dashboard, chart-ready
snapshot API, local chart MVP, EN/KO/EL frontend text, one-command install,
one-command uninstall, and performance evidence. The 2026-06-12 hardening gate
adds browser screenshots, local-only network checks, CSRF/read-only denial
evidence, and final smoke proof before this surface is treated as shippable.
Advanced research features remain backlog items until the operator surface is
trustworthy and fast.
