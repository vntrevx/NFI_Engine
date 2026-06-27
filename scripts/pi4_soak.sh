#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
duration_seconds="${NFI_ENGINE_PI4_SOAK_SECONDS:-900}"
interval_seconds="${NFI_ENGINE_PI4_SOAK_INTERVAL_SECONDS:-60}"
output_dir=""
project_name="${COMPOSE_PROJECT_NAME:-nfi-engine-pi4-rc}"
host_port="${NFI_ENGINE_HOST_PORT:-18080}"

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

print_help() {
  cat <<'HELP'
Usage: bash scripts/pi4_soak.sh [--duration-seconds N] [--interval-seconds N] [--output-dir PATH]

Runs repeated non-mutating Raspberry Pi 4 RC profile probes. The script records
per-iteration profile output plus a summary; it does not change CPU, fan,
Docker daemon, boot, sysctl, or trading settings.
HELP
}

number_arg() {
  local value="$1"
  local name="$2"
  case "$value" in
    "" | *[!0-9]*)
      die "PI4_SOAK_INVALID_NUMBER: $name=$value"
      ;;
  esac
  if [ "$value" -lt 1 ]; then
    die "PI4_SOAK_INVALID_NUMBER: $name=$value"
  fi
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help | -h)
      print_help
      exit 0
      ;;
    --duration-seconds)
      duration_seconds="${2:?PI4_SOAK_MISSING_VALUE: --duration-seconds}"
      shift 2
      ;;
    --interval-seconds)
      interval_seconds="${2:?PI4_SOAK_MISSING_VALUE: --interval-seconds}"
      shift 2
      ;;
    --output-dir)
      output_dir="${2:?PI4_SOAK_MISSING_VALUE: --output-dir}"
      shift 2
      ;;
    --project-name)
      project_name="${2:?PI4_SOAK_MISSING_VALUE: --project-name}"
      shift 2
      ;;
    --host-port)
      host_port="${2:?PI4_SOAK_MISSING_VALUE: --host-port}"
      shift 2
      ;;
    *)
      die "PI4_SOAK_UNKNOWN_ARGUMENT: $1"
      ;;
  esac
done

number_arg "$duration_seconds" duration_seconds
number_arg "$interval_seconds" interval_seconds

if [ -z "$output_dir" ]; then
  output_dir=".omo/evidence/pi4-soak-$(date -u +%Y%m%dT%H%M%SZ)"
fi

mkdir -p "$output_dir"
summary_path="$output_dir/summary.txt"
start_epoch="$(date +%s)"
end_epoch=$((start_epoch + duration_seconds))
iteration=0
pass_count=0
block_count=0

printf 'soak=pi4\n' | tee "$summary_path"
printf 'duration_seconds=%s\n' "$duration_seconds" | tee -a "$summary_path"
printf 'interval_seconds=%s\n' "$interval_seconds" | tee -a "$summary_path"
printf 'project_name=%s\n' "$project_name" | tee -a "$summary_path"
printf 'host_port=%s\n' "$host_port" | tee -a "$summary_path"

while [ "$(date +%s)" -lt "$end_epoch" ]; do
  iteration=$((iteration + 1))
  output_path="$output_dir/profile-$(printf '%04d' "$iteration").txt"
  status="pass"
  if ! COMPOSE_PROJECT_NAME="$project_name" NFI_ENGINE_HOST_PORT="$host_port" \
    bash "$repo_root/scripts/pi4_rc_profile.sh" --output "$output_path"; then
    status="block"
  fi
  if [ "$status" = "pass" ]; then
    pass_count=$((pass_count + 1))
  else
    block_count=$((block_count + 1))
  fi
  printf 'iteration=%s status=%s output=%s\n' "$iteration" "$status" "$output_path" \
    | tee -a "$summary_path"
  if [ "$(date +%s)" -ge "$end_epoch" ]; then
    break
  fi
  sleep "$interval_seconds"
done

printf 'iterations=%s\n' "$iteration" | tee -a "$summary_path"
printf 'pass_count=%s\n' "$pass_count" | tee -a "$summary_path"
printf 'block_count=%s\n' "$block_count" | tee -a "$summary_path"

if [ "$block_count" -gt 0 ]; then
  exit 1
fi
