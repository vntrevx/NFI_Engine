#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
credentials_dir="${NFI_ENGINE_TESTNET_CREDENTIALS_DIR:-.runtime/secrets}"
credential_file="${NFI_ENGINE_TESTNET_CREDENTIALS_FILE:-}"
legacy_credential_file=".runtime/secrets/exchange-wallet.env"
credential_file_override=false
init_template=false
output_path=""
runtime_dir="${NFI_ENGINE_TESTNET_PROBE_RUNTIME_DIR:-.runtime/testnet-credential-probe}"
priority_modes="binance:futures bybit:futures okx:futures bitget:futures"
selected_exchange=""

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

print_help() {
  cat <<'HELP'
Usage: bash scripts/testnet_credential_probe.sh [--credentials-dir DIR] [--credentials-file PATH] [--exchange EXCHANGE] [--init-template] [--output PATH]

Runs a secret-safe priority-exchange testnet credential probe. It never prints
credential values. If no owner-only credential file with recognized fields is
available, it reports blocked-no-key and only runs report-only runtime checks.
Pass --exchange binance for the owner-primary lane. Use bybit, okx, or bitget
only when collecting a redacted issue-driven expansion report.

Default per-exchange files:
  .runtime/secrets/testnet-binance.env
  .runtime/secrets/testnet-bybit.env
  .runtime/secrets/testnet-okx.env
  .runtime/secrets/testnet-bitget.env
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
      credential_file_override=true
      shift 2
      ;;
    --credentials-dir)
      credentials_dir="${2:?TESTNET_PROBE_MISSING_VALUE: --credentials-dir}"
      shift 2
      ;;
    --exchange)
      selected_exchange="$(printf '%s' "${2:?TESTNET_PROBE_MISSING_VALUE: --exchange}" | tr '[:upper:]' '[:lower:]')"
      shift 2
      ;;
    --init-template)
      init_template=true
      shift
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

active_priority_modes() {
  if [ -z "$selected_exchange" ]; then
    printf '%s\n' "$priority_modes"
    return
  fi
  for mode in $priority_modes; do
    exchange="${mode%%:*}"
    if [ "$exchange" = "$selected_exchange" ]; then
      printf '%s\n' "$mode"
      return
    fi
  done
  die "TESTNET_PROBE_UNSUPPORTED_EXCHANGE: $selected_exchange"
}

validate_selected_exchange() {
  if [ -z "$selected_exchange" ]; then
    return
  fi
  for mode in $priority_modes; do
    exchange="${mode%%:*}"
    if [ "$exchange" = "$selected_exchange" ]; then
      return
    fi
  done
  die "TESTNET_PROBE_UNSUPPORTED_EXCHANGE: $selected_exchange"
}

template_fields() {
  case "$1" in
    okx | bitget)
      printf '%s\n' api_key api_secret passphrase
      ;;
    *)
      printf '%s\n' api_key api_secret
      ;;
  esac
}

write_template() {
  mkdir -p "$credentials_dir"
  chmod 700 "$credentials_dir"
  for mode in $(active_priority_modes); do
    exchange="${mode%%:*}"
    template_file="$credentials_dir/testnet-$exchange.env"
    if [ -f "$template_file" ]; then
      chmod 600 "$template_file"
      printf 'template=preserved exchange=%s file=%s mode=600\n' "$exchange" "$template_file"
      continue
    fi
    umask 077
    template_fields "$exchange" | sed 's/$/=/' > "$template_file"
    chmod 600 "$template_file"
    printf 'template=created exchange=%s file=%s mode=600\n' "$exchange" "$template_file"
  done
}

credential_file_for_exchange() {
  exchange="$1"
  if [ "$credential_file_override" = true ]; then
    printf '%s\n' "$credential_file"
    return
  fi
  exchange_file="$credentials_dir/testnet-$exchange.env"
  if [ -f "$exchange_file" ]; then
    printf '%s\n' "$exchange_file"
    return
  fi
  if [ -n "$credential_file" ]; then
    printf '%s\n' "$credential_file"
    return
  fi
  printf '%s\n' "$legacy_credential_file"
}

field_names() {
  file_path="$1"
  if [ ! -f "$file_path" ]; then
    return
  fi
  sed -n 's/^[[:space:]]*\([A-Za-z_][A-Za-z0-9_]*\)[[:space:]]*=.*/\1/p' "$file_path" \
    | sort \
    | paste -sd ','
}

non_empty_field_names() {
  file_path="$1"
  if [ ! -f "$file_path" ]; then
    return
  fi
  awk -F= '
    /^[[:space:]]*#/ { next }
    /^[[:space:]]*$/ { next }
    {
      key=$1
      value=$0
      sub(/^[^=]*=/, "", value)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", key)
      gsub(/^[[:space:]]+|[[:space:]]+$/, "", value)
      if (key != "" && value != "") print key
    }
  ' "$file_path" | sort | paste -sd ','
}

credential_status_for_file() {
  file_path="$1"
  if [ ! -f "$file_path" ]; then
    printf 'missing\n'
    return
  fi
  if [ "$(stat -c '%a' "$file_path")" != "600" ]; then
    printf 'unsafe-mode\n'
    return
  fi
  if [ -z "$(non_empty_field_names "$file_path")" ]; then
    printf 'blocked-no-key\n'
    return
  fi
  printf 'present\n'
}

if [ "$init_template" = true ]; then
  validate_selected_exchange
  write_template
  exit 0
fi

validate_selected_exchange

printf 'probe=testnet-credential\n'
printf 'credentials_dir=%s\n' "$credentials_dir"
printf 'selected_exchange=%s\n' "${selected_exchange:-all}"
printf 'secrets=redacted\n'

tmp_dir="$(mktemp -d "${runtime_dir%/}/probe.XXXXXX")"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

for mode in $(active_priority_modes); do
  exchange="${mode%%:*}"
  trading_mode="${mode##*:}"
  probe_credential_file="$(credential_file_for_exchange "$exchange")"
  credential_status="$(credential_status_for_file "$probe_credential_file")"
  credential_fields="$(field_names "$probe_credential_file")"
  credential_non_empty_fields="$(non_empty_field_names "$probe_credential_file")"
  printf 'exchange=%s trading_mode=%s\n' "$exchange" "$trading_mode"
  printf 'credential_file=%s\n' "$probe_credential_file"
  printf 'credential_status=%s\n' "$credential_status"
  printf 'credential_fields=%s\n' "${credential_fields:-none}"
  printf 'credential_non_empty_fields=%s\n' "${credential_non_empty_fields:-none}"
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
    --credentials-file "$probe_credential_file" \
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
  pilot_output="$tmp_dir/$exchange-$trading_mode-pilot.txt"
  if ! uv run nfi-engine exchange testnet-pilot --config "$config_path" > "$pilot_output"; then
    sed 's/^/testnet_pilot\t/' "$pilot_output"
    printf 'real_testnet_action=blocked-pilot-command\n'
    continue
  fi
  sed 's/^/testnet_pilot\t/' "$pilot_output"
  if grep -q '^pilot_ready=true$' "$pilot_output"; then
    uv run nfi-engine exchange testnet-execute \
      --config "$config_path" \
      | sed 's/^/testnet_execute\t/'
    printf 'real_testnet_action=report-only-no-real-order\n'
    continue
  fi
  printf 'real_testnet_action=blocked-pilot\n'
done
