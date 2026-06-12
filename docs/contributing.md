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

Use focused tests first, then run the broader gate touched by your change:

```bash
uv run ruff format --check .
uv run ruff check .
uv run basedpyright
uv run pytest -q
```

User-visible or hot-path changes need manual evidence under `.omo/evidence/`.
For performance work, include benchmark evidence with machine metadata, workload
label, measured result, and whether a public comparison claim is allowed. Normal
M2 contribution work must not require a local Freqtrade install.
See [performance.md](performance.md) for the M2 benchmark command and regression
gate.

## Documentation Rules

Docs should make the simplest safe path obvious:

- Install first with `bash scripts/install.sh --yes --paper --testnet`.
- Browser login uses the token in `.runtime/docker.env`; do not print token
  values in examples or support artifacts.
- Open `http://127.0.0.1:18080/`.
- Use Settings for Simple Mode and write-only credential entry.
- Use Logs for error codes, correlation IDs, and support report export.
- Use `bash scripts/uninstall.sh --yes` for Safe Uninstall.
- Use `bash scripts/uninstall.sh --purge --yes` only for Destructive Purge.

Manual developer commands belong after the operator path, not before it.
