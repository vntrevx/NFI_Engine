#!/usr/bin/env bash
set -euo pipefail

mkdir -p .omo/evidence
docker_cleanup_needed=0
dry_run_runtime_dir=""
real_runtime_dir=""
real_project_name="nfi-engine-final-smoke"
real_host_port="${NFI_ENGINE_FINAL_SMOKE_HOST_PORT:-18180}"

cleanup_final_smoke() {
  if [[ -n "${dry_run_runtime_dir}" ]]; then
    rm -rf -- "${dry_run_runtime_dir}"
  fi
  if [[ "${docker_cleanup_needed}" -eq 1 ]]; then
    bash scripts/uninstall.sh --purge --yes --runtime-dir "${real_runtime_dir}/runtime" --project-name "${real_project_name}" >/dev/null 2>&1 || true
  fi
  if [[ -n "${real_runtime_dir}" ]]; then
    rm -rf -- "${real_runtime_dir}"
  fi
}

trap cleanup_final_smoke EXIT

uv run nfi-engine --help | tee .omo/evidence/final-cli-help.txt
uv run nfi-engine config validate --config examples/futures-paper.yaml | tee .omo/evidence/final-config-validate.txt
uv run nfi-engine preflight check --profile local-paper --config examples/spot-paper.yaml | tee .omo/evidence/final-preflight.txt
uv run nfi-engine backtest --config examples/spot-paper.yaml --timerange 2026-01-01:2026-01-07 --output .omo/evidence/final-backtest.json | tee .omo/evidence/final-backtest.txt
uv run nfi-engine validate walk-forward --config examples/spot-paper.yaml --splits 3 --output .omo/evidence/final-walk-forward.json | tee .omo/evidence/final-walk-forward.txt
uv run nfi-engine paper-run --config examples/futures-paper.yaml --ticks tests/fixtures/ticks/btc_usdt_futures.jsonl --max-events 25 | tee .omo/evidence/final-paper-run.txt
uv run nfi-engine strategy inspect --config examples/x7-futures-paper.yaml --strategy nfi_engine.strategy.nfi_x7:X7NativeStrategy --json | tee .omo/evidence/final-x7-strategy-inspect.json
python3 -m json.tool .omo/evidence/final-x7-strategy-inspect.json >/dev/null
uv run python -c 'import sys; from nfi_engine.strategy.nfi_x7 import X7NativeStrategy, build_x7_import_profile; X7NativeStrategy(); profile = build_x7_import_profile(tuple(sys.modules)); loaded = ",".join(profile.loaded_forbidden_runtime_modules) or "none"; print(f"loaded_forbidden_runtime_modules={loaded}"); print(f"has_forbidden_runtime_modules_loaded={str(profile.has_forbidden_runtime_modules_loaded).lower()}")' | tee .omo/evidence/final-x7-forbidden-runtime-modules.txt
grep -q "loaded_forbidden_runtime_modules=none" .omo/evidence/final-x7-forbidden-runtime-modules.txt
uv run python scripts/release_wording_scan.py | tee .omo/evidence/final-release-wording-scan.txt
grep -q "violations=0" .omo/evidence/final-release-wording-scan.txt
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
uv run pytest -q tests/e2e/test_i18n_ui.py tests/e2e/test_home_ui.py tests/e2e/test_api_surface.py tests/e2e/test_benchmark_cli.py | tee .omo/evidence/final-m2-focused-tests.txt
bash scripts/benchmark_m2.sh | tee .omo/evidence/final-m2-benchmark.txt
python3 -m json.tool .omo/evidence/m2-benchmark.json >/dev/null
dry_run_runtime_dir="$(mktemp -d)"
bash scripts/install.sh --yes --paper --testnet --dry-run --runtime-dir "${dry_run_runtime_dir}/runtime" | tee .omo/evidence/final-install-dry-run.txt
bash scripts/uninstall.sh --yes --dry-run --runtime-dir "${dry_run_runtime_dir}/runtime" | tee .omo/evidence/final-uninstall-safe-dry-run.txt
mkdir -p "${dry_run_runtime_dir}/purge-runtime"
printf 'nfi-engine-runtime=1\n' > "${dry_run_runtime_dir}/purge-runtime/.nfi-engine-runtime"
bash scripts/uninstall.sh --purge --yes --dry-run --runtime-dir "${dry_run_runtime_dir}/purge-runtime" | tee .omo/evidence/final-uninstall-purge-dry-run.txt
rm -rf -- "${dry_run_runtime_dir}"
dry_run_runtime_dir=""
real_runtime_dir="$(mktemp -d)"
bash scripts/install.sh --yes --paper --testnet --runtime-dir "${real_runtime_dir}/runtime" --project-name "${real_project_name}" --host-port "${real_host_port}" | tee .omo/evidence/final-docker-install.txt
docker_cleanup_needed=1
api_token="$(grep '^NFI_ENGINE_API_TOKEN=' "${real_runtime_dir}/runtime/docker.env" | cut -d= -f2-)"
if [[ -z "${api_token}" ]]; then
  printf "missing generated API token\n" >&2
  exit 1
fi
curl -fsS "http://127.0.0.1:${real_host_port}/api/v1/ping" | tee .omo/evidence/final-docker-ping.json
unauth_status="$(
  curl -sS \
    -o .omo/evidence/final-dashboard-snapshot-unauthenticated.json \
    -w '%{http_code}' \
    "http://127.0.0.1:${real_host_port}/api/v1/dashboard/snapshot"
)"
printf '%s\n' "${unauth_status}" | tee .omo/evidence/final-dashboard-snapshot-unauthenticated.status
[[ "${unauth_status}" == "401" || "${unauth_status}" == "403" ]]
curl -fsS -H "Authorization: Bearer ${api_token}" "http://127.0.0.1:${real_host_port}/" -o .omo/evidence/final-home.html
curl -fsS -H "Authorization: Bearer ${api_token}" "http://127.0.0.1:${real_host_port}/api/v1/dashboard/snapshot" -o .omo/evidence/final-dashboard-snapshot.json
grep -q 'data-testid="home-root"' .omo/evidence/final-home.html
grep -q 'data-testid="home-chart-shell"' .omo/evidence/final-home.html
python3 -m json.tool .omo/evidence/final-dashboard-snapshot.json >/dev/null
bash scripts/uninstall.sh --yes --runtime-dir "${real_runtime_dir}/runtime" --project-name "${real_project_name}" | tee .omo/evidence/final-uninstall-safe.txt
test -e "${real_runtime_dir}/runtime/config/futures-paper.yaml"
bash scripts/uninstall.sh --purge --yes --runtime-dir "${real_runtime_dir}/runtime" --project-name "${real_project_name}" | tee .omo/evidence/final-uninstall-purge.txt
docker_cleanup_needed=0
test ! -e "${real_runtime_dir}/runtime"
rm -rf -- "${real_runtime_dir}"
real_runtime_dir=""
printf "final smoke complete\n" | tee .omo/evidence/final-smoke-summary.txt
