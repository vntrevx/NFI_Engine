#!/usr/bin/env bash
set -euo pipefail

mkdir -p .omo/evidence

uv run nfi-engine --help | tee .omo/evidence/final-cli-help.txt
uv run nfi-engine config validate --config examples/futures-paper.yaml | tee .omo/evidence/final-config-validate.txt
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml | tee .omo/evidence/final-preflight.txt
uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/final-backtest.json | tee .omo/evidence/final-backtest.txt
uv run nfi-engine validate walk-forward --config examples/spot-paper.yaml --splits 3 --output .omo/evidence/final-walk-forward.json | tee .omo/evidence/final-walk-forward.txt
uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 25 | tee .omo/evidence/final-paper-run.txt
uv run nfi-engine plugins list --config examples/futures-paper.yaml | tee .omo/evidence/final-plugins.txt
uv run nfi-engine circuit-breaker simulate --config tests/fixtures/config/daily-loss-limit.yaml | tee .omo/evidence/final-circuit-breaker.txt
uv run nfi-engine notify test --config examples/futures-paper.yaml --channel jsonl --message final-smoke --output .omo/evidence/final-notify.jsonl | tee .omo/evidence/final-notify.txt
set +e
uv run nfi-engine sandbox check --strategy tests.fixtures.strategies.unsafe:EnvReadingStrategy 2>&1 | tee .omo/evidence/final-sandbox.txt
sandbox_status=${PIPESTATUS[0]}
set -e
if [[ "${sandbox_status}" -ne 1 ]]; then
  printf "expected sandbox violation exit 1, got %s\n" "${sandbox_status}" >&2
  exit 1
fi
grep -q "SANDBOX_VIOLATION" .omo/evidence/final-sandbox.txt
uv run nfi-engine db migrate --dry-run --database tests/fixtures/db/v0.sqlite | tee .omo/evidence/final-db-migrate.txt
uv run nfi-engine config migrate --dry-run --config tests/fixtures/config/v0-config.yaml | tee .omo/evidence/final-config-migrate.txt
uv run nfi-engine backup create --config examples/futures-paper.yaml --output .omo/evidence/final-backup.zip | tee .omo/evidence/final-backup-create.txt
uv run nfi-engine backup verify .omo/evidence/final-backup.zip | tee .omo/evidence/final-backup-verify.txt
uv run nfi-engine backup restore --dry-run .omo/evidence/final-backup.zip | tee .omo/evidence/final-restore-dry-run.txt
uv run nfi-engine exchange reconcile --config examples/futures-paper.yaml --dry-run --fixture tests/fixtures/exchange/reconcile_match.json | tee .omo/evidence/final-reconcile.txt
uv run nfi-engine pairlist validate --config examples/futures-paper.yaml --output .omo/evidence/final-pairlist.json | tee .omo/evidence/final-pairlist.txt
uv run nfi-engine simulate fills --scenario tests/fixtures/simulator/partial_fill_latency.yaml --output .omo/evidence/final-fill-sim.json | tee .omo/evidence/final-fill-sim.txt
printf "final smoke complete\n" | tee .omo/evidence/final-smoke-summary.txt
