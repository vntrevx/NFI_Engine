#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
project_name="${COMPOSE_PROJECT_NAME:-nfi-engine-pi4-rc}"
host_port="${NFI_ENGINE_HOST_PORT:-18080}"
min_cpu_max_khz=1800000
max_temp_c=75
output_path=""
blocks=""
warnings=""

die() {
  printf '%s\n' "$1" >&2
  exit 1
}

append_reason() {
  local current="$1"
  local reason="$2"
  if [ -z "$current" ]; then
    printf '%s' "$reason"
    return
  fi
  printf '%s,%s' "$current" "$reason"
}

block() {
  blocks="$(append_reason "$blocks" "$1")"
}

warn() {
  warnings="$(append_reason "$warnings" "$1")"
}

read_file_or_unknown() {
  local path="$1"
  if [ -r "$path" ]; then
    tr -d '\000' < "$path"
    return
  fi
  printf 'unknown'
}

validate_host_port() {
  case "$host_port" in
    "" | *[!0-9]*)
      die "PI4_INVALID_HOST_PORT: $host_port"
      ;;
  esac
  if [ "$host_port" -lt 1 ] || [ "$host_port" -gt 65535 ]; then
    die "PI4_INVALID_HOST_PORT: $host_port"
  fi
}

print_help() {
  cat <<'HELP'
Usage: bash scripts/pi4_rc_profile.sh [--project-name NAME] [--host-port PORT] [--output PATH]

Checks a reversible Raspberry Pi 4 release-candidate profile without changing
host CPU, fan, sysctl, journald, Docker daemon, or boot settings.

Blocks:
  PI4_CPU_MAX_REDUCED
  PI4_THROTTLED
  PI4_TEMP_HIGH
  PI4_DOCKER_MISSING
  PI4_DOCKER_COMPOSE_MISSING
  PI4_DOCKER_COMPOSE_CONFIG_FAILED
  PI4_COMPOSE_PUBLIC_BIND
  PI4_DOCKER_LOG_UNBOUNDED
  PI4_DOCKER_RESTART_POLICY_MISSING
  PI4_UV_MISSING
  PI4_PYTHON_MISSING
  PI4_DISK_LOW
HELP
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --help | -h)
      print_help
      exit 0
      ;;
    --project-name)
      project_name="${2:?PI4_MISSING_VALUE: --project-name}"
      shift 2
      ;;
    --host-port)
      host_port="${2:?PI4_MISSING_VALUE: --host-port}"
      shift 2
      ;;
    --min-cpu-max-khz)
      min_cpu_max_khz="${2:?PI4_MISSING_VALUE: --min-cpu-max-khz}"
      shift 2
      ;;
    --max-temp-c)
      max_temp_c="${2:?PI4_MISSING_VALUE: --max-temp-c}"
      shift 2
      ;;
    --output)
      output_path="${2:?PI4_MISSING_VALUE: --output}"
      shift 2
      ;;
    *)
      die "PI4_UNKNOWN_ARGUMENT: $1"
      ;;
  esac
done

validate_host_port

if [ -n "$output_path" ]; then
  mkdir -p "$(dirname "$output_path")"
  exec > >(tee "$output_path")
fi

model="$(read_file_or_unknown /proc/device-tree/model)"
governor="$(read_file_or_unknown /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor)"
cpu_max_khz="$(read_file_or_unknown /sys/devices/system/cpu/cpu0/cpufreq/scaling_max_freq)"
disk_available_kb="$(df -Pk "$repo_root" | awk 'NR == 2 {print $4}')"

if [ "$cpu_max_khz" != "unknown" ] && [ "$cpu_max_khz" -lt "$min_cpu_max_khz" ]; then
  block "PI4_CPU_MAX_REDUCED"
fi
if [ -n "$disk_available_kb" ] && [ "$disk_available_kb" -lt 1048576 ]; then
  block "PI4_DISK_LOW"
fi

if command -v vcgencmd >/dev/null 2>&1; then
  throttled="$(vcgencmd get_throttled)"
  temp_c="$(vcgencmd measure_temp | sed -E 's/temp=([0-9.]+).*/\1/')"
else
  throttled="unknown"
  temp_c="unknown"
  warn "PI4_VCGENCMD_MISSING"
fi

if [ "$throttled" != "unknown" ] && [ "$throttled" != "throttled=0x0" ]; then
  block "PI4_THROTTLED"
fi
if [ "$temp_c" != "unknown" ] && awk "BEGIN {exit !($temp_c > $max_temp_c)}"; then
  block "PI4_TEMP_HIGH"
fi

command -v uv >/dev/null 2>&1 || block "PI4_UV_MISSING"
command -v python3 >/dev/null 2>&1 || block "PI4_PYTHON_MISSING"
if ! command -v docker >/dev/null 2>&1; then
  block "PI4_DOCKER_MISSING"
else
  if ! docker compose version >/dev/null 2>&1; then
    block "PI4_DOCKER_COMPOSE_MISSING"
  else
    export NFI_ENGINE_HOST_PORT="$host_port"
    if ! compose_config="$(
      cd "$repo_root"
      docker compose --project-name "$project_name" config
    )"; then
      block "PI4_DOCKER_COMPOSE_CONFIG_FAILED"
    else
      if ! printf '%s\n' "$compose_config" | grep -Eq 'host_ip: 127\.0\.0\.1|127\.0\.0\.1:[^:]+:18080'; then
        block "PI4_COMPOSE_PUBLIC_BIND"
      fi
      if ! printf '%s\n' "$compose_config" | grep -q 'max-size: 10m'; then
        block "PI4_DOCKER_LOG_UNBOUNDED"
      fi
      if ! printf '%s\n' "$compose_config" | grep -Eq 'max-file: "?3"?'; then
        block "PI4_DOCKER_LOG_UNBOUNDED"
      fi
      if ! printf '%s\n' "$compose_config" | grep -q 'restart: unless-stopped'; then
        block "PI4_DOCKER_RESTART_POLICY_MISSING"
      fi
    fi
  fi
fi

if [ -z "$blocks" ]; then
  profile_status="pass"
else
  profile_status="block"
fi

printf 'profile_status=%s\n' "$profile_status"
printf 'blocks=%s\n' "${blocks:-none}"
printf 'warnings=%s\n' "${warnings:-none}"
printf 'model=%s\n' "$model"
printf 'cpu_governor=%s\n' "$governor"
printf 'cpu_max_khz=%s\n' "$cpu_max_khz"
printf 'min_cpu_max_khz=%s\n' "$min_cpu_max_khz"
printf 'throttled=%s\n' "$throttled"
printf 'temp_c=%s\n' "$temp_c"
printf 'max_temp_c=%s\n' "$max_temp_c"
printf 'disk_available_kb=%s\n' "$disk_available_kb"
printf 'host_port=%s\n' "$host_port"
printf 'compose_project=%s\n' "$project_name"
printf 'loopback_bind=127.0.0.1:%s:18080\n' "$host_port"
printf 'host_tuning=not_applied\n'
printf 'rollback_safe_uninstall=bash scripts/uninstall.sh --yes --project-name %s\n' "$project_name"
printf 'rollback_purge_preview=bash scripts/uninstall.sh --purge --yes --dry-run --project-name %s\n' "$project_name"

if [ "$profile_status" = "block" ]; then
  exit 1
fi
