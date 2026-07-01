# Contributing

NFI Engine is built as an original trading engine. Contributions should make the
operator product easier to run, safer to diagnose, faster to measure, and simpler
to maintain.

## Clean-Room Contribution Rules

Freqtrade is a behavior benchmark, not a source for implementation, UI, or docs
copy. Upstream NostalgiaForInfinity code is also not vendored here.

- Do not copy FreqUI navigation, layout, wording, colors, chart composition, or interaction flows.
- Do not copy Freqtrade or NFI source code into this repository.
- Use public behavior, public docs, black-box CLI/API output, and original tests as references.
- Keep public wording precise: "inspired by feature categories" is acceptable; parity or clone language is not.
- Do not add profit promises, live-money shortcuts, or unaudited exchange automation.

## Feature Design Rules

Every feature proposal should state the NFI Engine version of the idea before
implementation starts.

- Operator usability: reduce choices on the first screen and move rare controls behind Advanced Mode.
- Safety: make blocked actions explainable through stable machine codes and human-readable summaries.
- Performance: include benchmark evidence for hot paths before making speed claims.
- Modularity: keep each module boundary narrow and avoid expanding giant files.
- Maintenance: include logs, support report output, cleanup behavior, and rollback paths when the feature changes runtime state.

## Module Boundary Checklist

Before opening a large change, identify the owning package:

- `config` parses settings and redacts secrets.
- `setup` owns first-run config generation and write-only credential intake.
- `dashboard` owns read models for Home and charts.
- `api` exposes typed HTTP contracts.
- `ui` renders local HTML/CSS/JS and keeps contract tokens stable.
- `persistence` owns storage models and bounded repository reads.
- `risk`, `safety`, and `circuit_breakers` own live-risk gates.

If a feature needs more than one package, add tests at the boundary instead of
letting UI code reach into storage rows or raw config dictionaries.

## Test And Evidence Rules

Use focused tests first, then run the broader gate touched by your change. The
local shell surface is intentionally lightweight:

New behavioral gates and failure modes use TDD: capture the focused failing
proof before production edits, then keep the closest useful pytest layer green.
Tests-after is acceptable only for docs/status/evidence-only updates where no
runtime behavior changes. Pytest remains the main automated test surface; ruff,
basedpyright, CLI stdout, HTTP calls, browser QA, Docker smoke, and Pi4 shell
receipts are manual QA and evidence surfaces that support, but do not replace,
the behavioral test.

```bash
bash scripts/quality_gate.sh --docs-only
bash scripts/quality_gate.sh --coverage-only
bash scripts/quality_gate.sh --strict
```

`--docs-only` is the fast default for docs/governance edits. `--strict` runs the
existing full local gate:

```bash
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest -q
```

`--coverage-only` is a focused config/domain coverage smoke using existing
pytest-cov and coverage.py settings. It fails below `NFI_ENGINE_COVERAGE_MIN`
(default 80) without adding dependencies or heavyweight services.

User-visible or hot-path changes need manual evidence under `.omo/evidence/`.
For performance work, include benchmark evidence with machine metadata, workload
label, measured result, and whether a public comparison claim is allowed. Normal
M2 contribution work must not require a local Freqtrade install.
See [performance.md](performance.md) for the M2 benchmark command and regression
gate.

## Quality Budget Review

Coverage policy is touched-code coverage, not a vanity global percentage. New or
changed production behavior must have a direct test at the closest useful layer:
unit tests for pure rules, integration tests for adapters/storage, and e2e tests
for CLI/API/UI surfaces. When a touched package already has coverage tooling,
run the matching pytest-cov slice with a focused fail-under or record why that
slice is not meaningful yet.

Maintainability has the same budget pressure as tests. Treat 250 pure LOC as the
split pressure point for hand-edited source and test files: do not split files
solely for vanity, but do not add new behavior to an oversized file without
extracting the cohesive unit you are touching.

Performance Budget Review for hot-path changes:

- no repeated config parse in loops or request paths.
- no unbounded DB read.
- no unbounded candle/frame materialization.
- no UI payload growth without a cap.
- no new dependency without size/startup justification.
- no public speed, parity, or Pi4 claim without matching hardware, command,
  dataset, and budget evidence.

## Documentation Rules

Docs should make the simplest safe path obvious:

- Install first with `bash scripts/install.sh --yes --paper --testnet`.
- Browser login uses the token in `.runtime/docker.env`; do not print token
  values in examples or support artifacts.
- Open `http://127.0.0.1:18080/`.
- Use Settings for Simple Mode and write-only credential entry.
- Use Logs for error codes, correlation IDs, and support report export.
- Use the `Exchange test report` GitHub issue template for Binance-first
  testnet checks and other exchange expansion reports. Paste only redacted
  `runtime-check`, wallet balance, or `testnet-pilot` output.
  `--exchange bybit`, `--exchange okx`, and `--exchange bitget` are issue
  report inputs, not claims that those lanes are owner-primary validated.
- Use `bash scripts/uninstall.sh --yes` for Safe Uninstall.
- Use `bash scripts/uninstall.sh --purge --yes` only for Destructive Purge.
- For public-facing docs and release wording, apply `docs/release-wording.md`:
  - Run `uv run python scripts/release_wording_scan.py` and require `violations=0`.
  - Keep release claims aligned to evidence paths under `.omo/evidence` or `.omo/ulw-loop/evidence`.
  - Rewrite any blocked phrasing before docs merge.
  - Treat "native NFI-shaped X7 runtime", "superior/better", "parity", and "live-money" claims as release-critical until evidence-backed.
  - Do not add milestone-ready announcements that imply guarantee, completeness, or unproved profit behavior.

Manual developer commands belong after the operator path, not before it.
