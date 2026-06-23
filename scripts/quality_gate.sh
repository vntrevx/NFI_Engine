#!/usr/bin/env bash
set -euo pipefail

mode="docs-only"
coverage_min="${NFI_ENGINE_COVERAGE_MIN:-80}"

usage() {
  cat <<'EOF'
Usage: bash scripts/quality_gate.sh [--docs-only|--strict|--coverage-only|--help]

Modes:
  --docs-only       Fast governance slice. This is the default.
  --strict          Full local strict gate: format, ruff, basedpyright, pytest.
  --coverage-only   Focused coverage smoke for config/domain unit tests.

Coverage:
  --coverage-only uses pytest-cov and fails below NFI_ENGINE_COVERAGE_MIN.
  Default NFI_ENGINE_COVERAGE_MIN is 80.
EOF
}

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

run() {
  printf '+'
  for arg in "$@"; do
    printf ' %q' "$arg"
  done
  printf '\n'
  "$@"
}

if [ "$#" -gt 1 ]; then
  die "QUALITY_GATE_UNKNOWN_ARGUMENTS: pass exactly one mode or --help"
fi

if [ "$#" -eq 1 ]; then
  case "$1" in
    --docs-only)
      mode="docs-only"
      ;;
    --strict)
      mode="strict"
      ;;
    --coverage-only)
      mode="coverage-only"
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "QUALITY_GATE_UNKNOWN_ARGUMENT: $1"
      ;;
  esac
fi

case "$mode" in
  docs-only)
    run bash -n scripts/quality_gate.sh
    run uv run ruff check \
      pyproject.toml \
      docs/contributing.md \
      README.md \
      README.ko.md \
      scripts/quality_gate.sh \
      tests/unit/docs/test_operator_docs.py
    run uv run ruff format --check tests/unit/docs/test_operator_docs.py
    run uv run pytest tests/unit/docs/test_operator_docs.py -q
    ;;
  strict)
    run uv run ruff format --check .
    run uv run ruff check .
    run uv run basedpyright
    run uv run pytest -q
    ;;
  coverage-only)
    run uv run pytest \
      tests/unit/domain \
      tests/unit/config \
      -q \
      --cov=src/nfi_engine/domain \
      --cov=src/nfi_engine/config \
      --cov-report=term \
      --cov-fail-under="$coverage_min"
    ;;
  *)
    die "QUALITY_GATE_INVALID_MODE: $mode"
    ;;
esac
