#!/usr/bin/env bash
set -euo pipefail

output=".omo/evidence/m2-benchmark.json"
mkdir -p ".omo/evidence"

uv run nfi-engine benchmark m2 --output "$output" "$@"
python3 -m json.tool .omo/evidence/m2-benchmark.json >/dev/null
printf 'benchmark_output=%s\n' "$output"
