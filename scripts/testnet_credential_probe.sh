#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
credential_file="${NFI_ENGINE_TESTNET_CREDENTIALS_FILE:-.runtime/secrets/exchange-wallet.env}"
output_path=""
runtime_dir="${NFI_ENGINE_TESTNET_PROBE_RUNTIME_DIR:-.runtime/testnet-credential-probe}"
priority_modes="binance:futures bybit:futures okx:futures bitget:futures"

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

print_help() {
  cat <<'HELP'
Usage: bash scripts/testnet_credential_probe.sh [--credentials-file PATH] [--output PATH]

Runs a secret-safe priority-exchange testnet credential probe. It never prints
credential values. If no owner-only credential file with recognized fields is
available, it reports blocked-no-key and only runs report-only runtime checks.
HELP
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help | -h)
      print_help
      exit 0
      ;;
    --credentials-file)
      credential_file="${2:?TESTNET_PROBE_MISSING_VALUE: --credentials-file}"
      shift 2
      ;;
    --output)
      output_path="${2:?TESTNET_PROBE_MISSING_VALUE: --output}"
      shift 2
      ;;
    *)
      die "TESTNET_PROBE_UNKNOWN_ARGUMENT: $1"
      ;;
  esac
done

if [ -n "$output_path" ]; then
  mkdir -p "$(dirname "$output_path")"
  exec > >(tee "$output_path")
fi

cd "$repo_root"
mkdir -p "$runtime_dir"

field_names() {
  if [ ! -f "$credential_file" ]; then
    return
  fi
  sed -n 's/^[[:space:]]*\([A-Za-z_][A-Za-z0-9_]*\)[[:space:]]*=.*/\1/p' "$credential_file" \
    | sort \
    | paste -sd ','
}

credential_status="present"
credential_fields="$(field_names)"
if [ ! -f "$credential_file" ]; then
  credential_status="missing"
elif [ "$(stat -c '%a' "$credential_file")" != "600" ]; then
  credential_status="unsafe-mode"
elif [ -z "$credential_fields" ]; then
  credential_status="blocked-no-key"
fi

printf 'probe=testnet-credential\n'
printf 'credential_file=%s\n' "$credential_file"
printf 'credential_status=%s\n' "$credential_status"
printf 'credential_fields=%s\n' "${credential_fields:-none}"
printf 'secrets=redacted\n'

tmp_dir="$(mktemp -d "${runtime_dir%/}/probe.XXXXXX")"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

for mode in $priority_modes; do
  exchange="${mode%%:*}"
  trading_mode="${mode##*:}"
  printf 'exchange=%s trading_mode=%s\n' "$exchange" "$trading_mode"
  if [ "$credential_status" != "present" ]; then
    uv run nfi-engine exchange runtime-check \
      --exchange "$exchange" \
      --trading-mode "$trading_mode" \
      --format text \
      | sed 's/^/runtime_check\t/'
    printf 'real_testnet_action=blocked-no-key\n'
    continue
  fi
  config_path="$tmp_dir/$exchange-$trading_mode.yaml"
  if ! uv run nfi-engine setup init \
    --config "$config_path" \
    --exchange "$exchange" \
    --trading-mode "$trading_mode" \
    --testnet \
    --credentials-file "$credential_file" \
    --non-interactive \
    --force \
    | sed 's/^/setup\t/'; then
    printf 'real_testnet_action=blocked-credential-shape\n'
    continue
  fi
  uv run nfi-engine exchange runtime-check \
    --config "$config_path" \
    --format text \
    | sed 's/^/runtime_check\t/'
  uv run nfi-engine exchange testnet-pilot \
    --config "$config_path" \
    | sed 's/^/testnet_pilot\t/'
  printf 'real_testnet_action=report-only-no-order\n'
done
